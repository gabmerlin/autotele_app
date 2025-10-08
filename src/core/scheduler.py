"""
Gestionnaire de planification des messages
"""
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from uuid import uuid4

from core.telegram_manager import TelegramManager
from utils.logger import get_logger
from utils.config import get_config


class ScheduledTask:
    """Représente une tâche de message planifié"""
    
    def __init__(self, task_id: str, session_id: str, account_name: str,
                 groups: List[Dict], message: str, schedule_times: List[datetime],
                 file_path: str = None):
        self.task_id = task_id
        self.session_id = session_id
        self.account_name = account_name
        self.groups = groups  # Liste de {id, title}
        self.message = message
        self.schedule_times = schedule_times if isinstance(schedule_times, list) else [schedule_times]  # Liste de dates/heures
        self.file_path = file_path
        self.status = "pending"  # pending, processing, completed, failed
        self.created_at = datetime.now()
        self.results = {}  # {group_id: {success: bool, error: str, sent_count: int}}
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire"""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "account_name": self.account_name,
            "groups": self.groups,
            "message": self.message[:200],  # Limiter la taille
            "schedule_times": [st.isoformat() for st in self.schedule_times],
            "file_path": self.file_path,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "results": self.results
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'ScheduledTask':
        """Crée depuis un dictionnaire"""
        # Support ancien format (schedule_time) et nouveau (schedule_times)
        if "schedule_times" in data:
            schedule_times = [datetime.fromisoformat(st) for st in data["schedule_times"]]
        elif "schedule_time" in data:
            schedule_times = [datetime.fromisoformat(data["schedule_time"])]
        else:
            schedule_times = [datetime.now()]
        
        task = ScheduledTask(
            data["task_id"],
            data["session_id"],
            data["account_name"],
            data["groups"],
            data["message"],
            schedule_times,
            data.get("file_path")
        )
        task.status = data.get("status", "pending")
        task.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        task.results = data.get("results", {})
        return task


class MessageScheduler:
    """Gestionnaire de planification des messages"""
    
    def __init__(self, telegram_manager: TelegramManager):
        self.telegram_manager = telegram_manager
        self.logger = get_logger()
        self.config = get_config()
        
        # Fichier de stockage des tâches
        self.tasks_file = Path("config/scheduled_tasks.json")
        self.tasks: Dict[str, ScheduledTask] = {}
        self._load_tasks()
        
        # Task de vérification périodique
        self._check_task = None
        self._running = False
        
        # CONFIGURATION OPTIMISÉE : 27 requêtes/seconde
        # Pas de quota par minute car les messages programmés sont moins restrictifs
    
    def _load_tasks(self):
        """Charge les tâches depuis le fichier"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = ScheduledTask.from_dict(task_data)
                        # Ne charger que les tâches pending ou processing
                        if task.status in ["pending", "processing"]:
                            self.tasks[task.task_id] = task
            except Exception as e:
                self.logger.error(f"Erreur chargement tâches: {e}")
    
    def _save_tasks(self):
        """Sauvegarde les tâches dans le fichier"""
        try:
            self.tasks_file.parent.mkdir(exist_ok=True)
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                tasks_data = [task.to_dict() for task in self.tasks.values()]
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde tâches: {e}")
    
    def create_task(self, session_id: str, account_name: str, groups: List[Dict],
                   message: str, schedule_times: List[datetime], file_path: str = None) -> str:
        """
        Crée UNE tâche pour tous les groupes avec plusieurs dates/heures
        Retourne l'ID de la tâche
        """
        try:
            # Support ancien format (schedule_time unique)
            if not isinstance(schedule_times, list):
                schedule_times = [schedule_times]
            
            # VÉRIFICATION : Limiter le nombre total de messages (protection contre abus)
            total_messages = len(groups) * len(schedule_times)
            max_messages_per_task = 500  # Limite augmentée pour 27 req/sec
            
            if total_messages > max_messages_per_task:
                error_msg = f"⚠️ TROP DE MESSAGES : {total_messages} messages (max: {max_messages_per_task})\n\n" \
                           f"Pour des performances optimales :\n" \
                           f"- Max recommandé : 500 messages par tâche\n" \
                           f"- Ou divise en plusieurs envois\n\n" \
                           f"Actuellement : {len(groups)} groupes × {len(schedule_times)} dates"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Vérifications
            max_groups = self.config.get("telegram.max_groups_warning", 50)
            if len(groups) > max_groups:
                self.logger.warning(f"Attention : {len(groups)} groupes sélectionnés (> {max_groups})")
            
            # Créer UNE seule tâche pour tous les groupes et toutes les dates
            task_id = str(uuid4())
            task = ScheduledTask(
                task_id, session_id, account_name, groups,
                message, schedule_times, file_path
            )
            
            self.tasks[task_id] = task
            self._save_tasks()
            
            total_messages = len(groups) * len(schedule_times)
            self.logger.info(f"📋 Tâche créée: {len(groups)} groupes × {len(schedule_times)} dates = {total_messages} messages")
            
            # Logger dans l'historique (utiliser la première date pour l'historique)
            self.logger.log_scheduled_message(
                account_name,
                [g.get("name") or g.get("title", "Inconnu") for g in groups],
                message,
                schedule_times[0] if schedule_times else datetime.now()
            )
            
            return task_id
            
        except Exception as e:
            self.logger.error(f"Erreur create_task: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Récupère une tâche"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: str = None) -> List[ScheduledTask]:
        """Liste les tâches (filtrées par statut si spécifié)"""
        if status:
            return [t for t in self.tasks.values() if t.status == status]
        return list(self.tasks.values())
    
    def delete_task(self, task_id: str):
        """Supprime une tâche"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            self.logger.info(f"Tâche supprimée: {task_id}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Annule une tâche en cours"""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                old_status = task.status
                task.status = "cancelled"
                self._save_tasks()
                print(f"🚫 Tâche {task_id[:8]} annulée (était: {old_status})")
                self.logger.info(f"✅ Tâche annulée: {task_id}")
                return True
            else:
                self.logger.warning(f"⚠️ Tâche introuvable: {task_id}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Erreur annulation tâche {task_id}: {e}")
            return False
    
    def _cleanup_old_tasks(self):
        """Nettoie les anciennes tâches terminées/annulées (garde les 10 dernières de chaque type)"""
        try:
            # Séparer par statut
            completed_tasks = [(t.created_at, task_id) for task_id, t in self.tasks.items() if t.status == "completed"]
            cancelled_tasks = [(t.created_at, task_id) for task_id, t in self.tasks.items() if t.status == "cancelled"]
            failed_tasks = [(t.created_at, task_id) for task_id, t in self.tasks.items() if t.status == "failed"]
            
            # Garder seulement les 10 plus récentes de chaque type
            to_delete = []
            
            if len(completed_tasks) > 10:
                completed_tasks.sort()  # Trier par date
                to_delete.extend([task_id for _, task_id in completed_tasks[:-10]])  # Garder les 10 dernières
            
            if len(cancelled_tasks) > 10:
                cancelled_tasks.sort()
                to_delete.extend([task_id for _, task_id in cancelled_tasks[:-10]])
            
            if len(failed_tasks) > 10:
                failed_tasks.sort()
                to_delete.extend([task_id for _, task_id in failed_tasks[:-10]])
            
            # Supprimer les anciennes tâches
            if to_delete:
                for task_id in to_delete:
                    del self.tasks[task_id]
                self._save_tasks()
                print(f"🧹 {len(to_delete)} anciennes tâches nettoyées")
                self.logger.info(f"🧹 {len(to_delete)} anciennes tâches nettoyées")
                
        except Exception as e:
            self.logger.error(f"Erreur nettoyage tâches: {e}")
    
    async def execute_task(self, task_id: str):
        """
        Exécute une tâche : envoie les messages planifiés
        """
        task = self.tasks.get(task_id)
        if not task:
            self.logger.error(f"Tâche introuvable: {task_id}")
            return
        
        # VÉRIFICATION CRITIQUE : Ne JAMAIS exécuter une tâche annulée
        if task.status == "cancelled":
            print(f"🚫 Tâche {task_id[:8]} ANNULÉE - Ignorée")
            self.logger.info(f"🚫 Tâche {task_id} ignorée car annulée")
            return
        
        if task.status != "pending":
            print(f"⏭️ Tâche {task_id[:8]} déjà traitée (statut: {task.status})")
            self.logger.warning(f"Tâche déjà traitée: {task_id} (statut: {task.status})")
            return
        
        task.status = "processing"
        self._save_tasks()
        
        self.logger.info(f"Exécution tâche: {task_id}")
        
        # Récupérer le compte
        account = self.telegram_manager.get_account(task.session_id)
        if not account or not account.is_connected:
            task.status = "failed"
            self.logger.error(f"Compte non disponible pour tâche {task_id}")
            self._save_tasks()
            return
        
        # ENVOI OPTIMISÉ : UN PASSAGE PAR GROUPE, TOUTES LES DATES EN UNE FOIS
        success_count = 0
        failed_count = 0
        total_groups = len(task.groups)
        total_dates = len(task.schedule_times)
        
        # Vérifier qu'il y a au moins un groupe
        if not task.groups or total_groups == 0:
            self.logger.error(f"Tâche {task_id} sans groupe")
            task.status = "failed"
            self._save_tasks()
            return
        
        total_messages = total_groups * total_dates
        self.logger.info(f"🚀 Début envoi: {total_groups} groupes × {total_dates} dates = {total_messages} messages")
        print(f"🚀 ENVOI OPTIMISÉ: {total_groups} groupes × {total_dates} dates = {total_messages} messages")
        
        # Traiter chaque groupe UNE SEULE FOIS avec toutes ses dates
        for index, group in enumerate(task.groups, 1):
            try:
                # VÉRIFIER si la tâche a été annulée pendant l'exécution
                if task.status == "cancelled":
                    print(f"\n🚫 Tâche annulée pendant l'exécution - Arrêt immédiat")
                    self.logger.info(f"🚫 Tâche {task_id} annulée pendant l'exécution")
                    return
                
                group_id = group.get("id")
                group_title = group.get("name") or group.get("title", "Inconnu")
                
                if not group_id:
                    self.logger.error(f"Groupe sans ID: {group_title}")
                    failed_count += 1
                    continue
                
                # Afficher la progression (une seule fois par groupe)
                print(f"📤 [{index}/{total_groups}] {group_title} - {total_dates} messages...", end='', flush=True)
                
                # Envoyer TOUS les messages de ce groupe (toutes les dates)
                group_success = 0
                group_failed = 0
                
                for schedule_time in task.schedule_times:
                    try:
                        success, error = await account.schedule_message(
                            group_id,
                            task.message,
                            schedule_time,
                            task.file_path
                        )
                        
                        if success:
                            group_success += 1
                        else:
                            group_failed += 1
                            
                            # DÉTECTION RATE LIMIT : ARRÊT IMMÉDIAT
                            if "rate limit" in error.lower() or "flood" in error.lower():
                                print(f"\n🛑 RATE LIMIT DÉTECTÉ - ARRÊT IMMÉDIAT DE LA TÂCHE")
                                self.logger.error(f"🛑 RATE LIMIT: {error}")
                                task.status = "failed"
                                self._save_tasks()
                                return  # ARRÊT TOTAL
                            
                            # Logger les autres erreurs
                            self.logger.error(f"❌ Échec {group_title} à {schedule_time.strftime('%H:%M')}: {error}")
                        
                        # DÉLAI OPTIMISÉ : 37ms entre messages = 27 requêtes/seconde
                        await asyncio.sleep(0.037)
                        
                    except Exception as e:
                        group_failed += 1
                        error_str = str(e)
                        
                        # DÉTECTION RATE LIMIT : ARRÊT IMMÉDIAT
                        if "rate limit" in error_str.lower() or "flood" in error_str.lower():
                            print(f"\n🛑 RATE LIMIT DÉTECTÉ - ARRÊT IMMÉDIAT DE LA TÂCHE")
                            self.logger.error(f"🛑 RATE LIMIT: {e}")
                            task.status = "failed"
                            self._save_tasks()
                            return  # ARRÊT TOTAL
                        
                        self.logger.error(f"❌ Erreur {group_title} à {schedule_time.strftime('%H:%M')}: {e}")
                
                # Sauvegarder les résultats du groupe
                task.results[str(group_id)] = {
                    "success": group_failed == 0,
                    "error": None if group_failed == 0 else f"{group_failed} échec(s)",
                    "group_title": group_title,
                    "sent_count": group_success,
                    "total_count": total_dates
                }
                
                if group_failed == 0:
                    success_count += 1
                    print(f" ✅ {group_success}/{total_dates}")  # Continuer sur la même ligne
                    self.logger.log_send_result(task_id, group_title, True)
                else:
                    failed_count += 1
                    print(f" ⚠️ {group_success}/{total_dates} ({group_failed} échecs)")
                    self.logger.log_send_result(task_id, group_title, False, f"{group_failed} échec(s)")
                
                # Petite pause entre groupes (pour stabilité)
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                print(f"❌ [{index}/{total_groups}] Erreur: {error_msg}")
                
                if group_id:
                    task.results[str(group_id)] = {
                        "success": False,
                        "error": error_msg,
                        "group_title": group_title,
                        "sent_count": 0,
                        "total_count": total_dates
                    }
                    self.logger.log_send_result(task_id, group_title, False, error_msg)
        
        total_sent = sum(r.get("sent_count", 0) for r in task.results.values())
        print(f"✅ Envoi terminé: {success_count}/{total_groups} groupes réussis - {total_sent}/{total_messages} messages envoyés")
        
        # Mettre à jour le statut
        if failed_count == 0:
            task.status = "completed"
        elif success_count == 0:
            task.status = "failed"
        else:
            task.status = "partial"
        
        self._save_tasks()
        
        self.logger.info(
            f"🚀 Tâche {task_id} TERMINÉE RAPIDEMENT: {success_count} succès, {failed_count} échecs"
        )
    
    async def check_pending_tasks(self):
        """Vérifie et exécute les tâches en attente"""
        now = datetime.now()
        
        # Nettoyer d'abord les anciennes tâches
        self._cleanup_old_tasks()
        
        # Filtrer UNIQUEMENT les tâches "pending" (ignorer cancelled, completed, failed, etc.)
        pending_tasks = [t for t in self.tasks.values() if t.status == "pending"]
        
        if not pending_tasks:
            return  # Pas de tâches à exécuter
        
        print(f"📋 {len(pending_tasks)} tâche(s) pending à traiter")
        self.logger.info(f"📋 Exécution de {len(pending_tasks)} tâche(s)")
        
        # Exécuter chaque tâche l'une après l'autre (stable)
        for task in pending_tasks:
            try:
                # VÉRIFIER ENCORE UNE FOIS avant d'exécuter (au cas où elle a été annulée entre-temps)
                if task.status != "pending":
                    print(f"⏭️ Tâche {task.task_id[:8]} ignorée (statut: {task.status})")
                    continue
                
                print(f"\n🔄 Traitement tâche {task.task_id[:8]}: {len(task.groups)} groupes × {len(task.schedule_times)} dates")
                await self.execute_task(task.task_id)
                
                # Petite pause entre les tâches
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"❌ Erreur tâche {task.task_id[:8]}: {e}")
                self.logger.error(f"Erreur exécution tâche {task.task_id}: {e}")
                # Marquer comme failed
                task.status = "failed"
                self._save_tasks()
        
        print(f"✅ Vérification terminée")
    
    async def start_scheduler(self):
        """Démarre le scheduler (vérification périodique)"""
        if self._running:
            self.logger.warning("⚠️ Scheduler déjà en cours d'exécution")
            return
        
        self._running = True
        print("✅ Scheduler démarré - Vérification toutes les 5 secondes")
        self.logger.info("✅ Scheduler démarré")
        
        iteration = 0
        while self._running:
            try:
                iteration += 1
                
                # Ne logger que toutes les minutes (pas à chaque itération)
                if iteration % 12 == 1:
                    print(f"🔄 Scheduler actif (tâches: {len(self.tasks)})")
                
                await self.check_pending_tasks()
                
            except Exception as e:
                print(f"❌ Erreur scheduler: {e}")
                self.logger.error(f"❌ Erreur dans le scheduler: {e}", exc_info=True)
            
            # Vérifier toutes les 5 secondes
            await asyncio.sleep(5)
    
    def stop_scheduler(self):
        """Arrête le scheduler"""
        self._running = False
        self.logger.info("Scheduler arrêté")
    
    def get_statistics(self) -> Dict:
        """Récupère des statistiques sur les tâches"""
        total = len(self.tasks)
        pending = len([t for t in self.tasks.values() if t.status == "pending"])
        processing = len([t for t in self.tasks.values() if t.status == "processing"])
        completed = len([t for t in self.tasks.values() if t.status == "completed"])
        failed = len([t for t in self.tasks.values() if t.status == "failed"])
        
        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed
        }
    
    def cleanup_old_tasks(self, days: int = 30):
        """Supprime les tâches terminées de plus de X jours"""
        cutoff = datetime.now() - timedelta(days=days)
        
        to_delete = []
        for task_id, task in self.tasks.items():
            if task.status in ["completed", "failed"] and task.created_at < cutoff:
                to_delete.append(task_id)
        
        for task_id in to_delete:
            del self.tasks[task_id]
        
        if to_delete:
            self._save_tasks()
            self.logger.info(f"{len(to_delete)} tâches anciennes supprimées")

