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
                 groups: List[Dict], message: str, schedule_time: datetime,
                 file_path: str = None):
        self.task_id = task_id
        self.session_id = session_id
        self.account_name = account_name
        self.groups = groups  # Liste de {id, title}
        self.message = message
        self.schedule_time = schedule_time
        self.file_path = file_path
        self.status = "pending"  # pending, processing, completed, failed
        self.created_at = datetime.now()
        self.results = {}  # {group_id: {success: bool, error: str}}
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire"""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "account_name": self.account_name,
            "groups": self.groups,
            "message": self.message[:200],  # Limiter la taille
            "schedule_time": self.schedule_time.isoformat(),
            "file_path": self.file_path,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "results": self.results
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'ScheduledTask':
        """Crée depuis un dictionnaire"""
        task = ScheduledTask(
            data["task_id"],
            data["session_id"],
            data["account_name"],
            data["groups"],
            data["message"],
            datetime.fromisoformat(data["schedule_time"]),
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
                   message: str, schedule_time: datetime, file_path: str = None) -> str:
        """
        Crée une nouvelle tâche de message planifié
        Retourne l'ID de la tâche
        """
        # Vérifications
        if schedule_time <= datetime.now():
            raise ValueError("L'heure de planification doit être dans le futur")
        
        max_groups = self.config.get("telegram.max_groups_warning", 50)
        if len(groups) > max_groups:
            self.logger.warning(f"Attention : {len(groups)} groupes sélectionnés (> {max_groups})")
        
        # Créer la tâche
        task_id = str(uuid4())
        task = ScheduledTask(
            task_id, session_id, account_name, groups,
            message, schedule_time, file_path
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        self.logger.info(f"Tâche créée: {task_id} - {len(groups)} groupes - {schedule_time}")
        
        # Logger dans l'historique
        self.logger.log_scheduled_message(
            account_name,
            [g["title"] for g in groups],
            message,
            schedule_time
        )
        
        return task_id
    
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
    
    async def execute_task(self, task_id: str):
        """
        Exécute une tâche : envoie les messages planifiés
        """
        task = self.tasks.get(task_id)
        if not task:
            self.logger.error(f"Tâche introuvable: {task_id}")
            return
        
        if task.status != "pending":
            self.logger.warning(f"Tâche déjà traitée: {task_id}")
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
        
        # Envoyer les messages planifiés dans chaque groupe
        success_count = 0
        failed_count = 0
        
        for group in task.groups:
            group_id = group["id"]
            group_title = group["title"]
            
            try:
                success, error = await account.schedule_message(
                    group_id,
                    task.message,
                    task.schedule_time,
                    task.file_path
                )
                
                task.results[str(group_id)] = {
                    "success": success,
                    "error": error,
                    "group_title": group_title
                }
                
                if success:
                    success_count += 1
                    self.logger.log_send_result(task_id, group_title, True)
                else:
                    failed_count += 1
                    self.logger.log_send_result(task_id, group_title, False, error)
                
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                task.results[str(group_id)] = {
                    "success": False,
                    "error": error_msg,
                    "group_title": group_title
                }
                self.logger.log_send_result(task_id, group_title, False, error_msg)
        
        # Mettre à jour le statut
        if failed_count == 0:
            task.status = "completed"
        elif success_count == 0:
            task.status = "failed"
        else:
            task.status = "partial"
        
        self._save_tasks()
        
        self.logger.info(
            f"Tâche {task_id} terminée: {success_count} succès, {failed_count} échecs"
        )
    
    async def check_pending_tasks(self):
        """Vérifie et exécute les tâches en attente"""
        now = datetime.now()
        
        for task in list(self.tasks.values()):
            if task.status == "pending" and task.schedule_time <= now:
                self.logger.info(f"Tâche prête à être exécutée: {task.task_id}")
                await self.execute_task(task.task_id)
    
    async def start_scheduler(self):
        """Démarre le scheduler (vérification périodique)"""
        if self._running:
            return
        
        self._running = True
        self.logger.info("Scheduler démarré")
        
        while self._running:
            try:
                await self.check_pending_tasks()
            except Exception as e:
                self.logger.error(f"Erreur dans le scheduler: {e}", exc_info=True)
            
            # Vérifier toutes les 30 secondes
            await asyncio.sleep(30)
    
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

