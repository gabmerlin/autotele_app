"""
Service de gestion des messages programmés.
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path

from core.telegram.account import TelegramAccount
from utils.logger import get_logger
from utils.constants import (
    TELEGRAM_MIN_DELAY_PER_CHAT,
    TELEGRAM_MIN_DELAY_BETWEEN_MESSAGES
)

logger = get_logger()


class MessageService:
    """Service pour gérer l'envoi de messages programmés."""
    
    @staticmethod
    async def send_scheduled_messages(
        account: TelegramAccount,
        group_ids: List[int],
        message: str,
        dates: List[datetime],
        file_path: Optional[str] = None,
        on_progress: Optional[callable] = None,
        cancelled_flag: Optional[Dict] = None
    ) -> Tuple[int, int, Set[int]]:
        """
        Envoie des messages programmés à plusieurs groupes sur plusieurs dates.
        
        Stratégie d'optimisation:
        - Parcourt chaque créneau horaire
        - Envoie le message à tous les groupes pour ce créneau
        - Respecte les rate limits:
            * 1 message/seconde/chat (prioritaire)
            * 25 messages/seconde au total (0.04s entre chaque envoi)
        
        Args:
            account: Compte Telegram à utiliser
            group_ids: Liste des IDs de groupes
            message: Message à envoyer
            dates: Liste des dates de planification
            file_path: Chemin du fichier à joindre (optionnel)
            on_progress: Callback pour suivre la progression (sent, total, skipped)
            cancelled_flag: Dict avec une clé 'value' pour annuler l'envoi
            
        Returns:
            Tuple[int, int, Set[int]]: (nb_envoyés, nb_skipped, groupes_en_erreur)
        """
        if not account.is_connected:
            raise ValueError("Le compte n'est pas connecté")
        
        total_groups = len(group_ids)
        total_dates = len(dates)
        total = total_groups * total_dates
        sent = 0
        skipped = 0
        failed_groups: Set[int] = set()
        
        # Tracker des derniers envois
        last_send_time: Dict[int, float] = {}
        last_global_send = 0.0
        
        logger.info(f"Début envoi: {total} messages sur {total_groups} groupes et {total_dates} créneaux")
        
        # Parcourir chaque créneau horaire
        for date_idx, dt in enumerate(dates, 1):
            # Vérifier l'annulation
            if cancelled_flag and cancelled_flag.get('value'):
                logger.info(f"Envoi annulé par l'utilisateur après {sent} messages")
                break
            
            # Envoyer ce créneau à tous les groupes
            for group_idx, group_id in enumerate(group_ids, 1):
                # Vérifier l'annulation
                if cancelled_flag and cancelled_flag.get('value'):
                    break
                
                # Skip les groupes qui ont déjà échoué
                if group_id in failed_groups:
                    skipped += 1
                    if on_progress:
                        on_progress(sent, total, skipped, failed_groups)
                    continue
                
                try:
                    # PROTECTION: Calculer le délai maximum à respecter
                    wait_time = 0.0
                    
                    # Protection 1: Rate limit par chat (2 sec/chat)
                    if group_id in last_send_time:
                        elapsed_chat = asyncio.get_event_loop().time() - last_send_time[group_id]
                        if elapsed_chat < TELEGRAM_MIN_DELAY_PER_CHAT:
                            wait_time = max(wait_time, TELEGRAM_MIN_DELAY_PER_CHAT - elapsed_chat)
                    
                    # Protection 2: Rate limit global (25 msg/sec = 0.04s entre envois)
                    if last_global_send > 0:
                        elapsed_global = asyncio.get_event_loop().time() - last_global_send
                        if elapsed_global < TELEGRAM_MIN_DELAY_BETWEEN_MESSAGES:
                            wait_time = max(wait_time, TELEGRAM_MIN_DELAY_BETWEEN_MESSAGES - elapsed_global)
                    
                    # Attendre si nécessaire (une seule fois, le max des deux)
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                    
                    # Envoyer le message
                    success, error = await account.schedule_message(
                        group_id,
                        message,
                        dt,
                        file_path
                    )
                    
                    # IMPORTANT: Toujours enregistrer l'heure, même en cas d'échec
                    # pour éviter les envois trop rapides après une erreur
                    current_time = asyncio.get_event_loop().time()
                    last_send_time[group_id] = current_time
                    last_global_send = current_time
                    
                    if success:
                        sent += 1
                        if on_progress:
                            on_progress(sent, total, skipped, failed_groups)
                    else:
                        # Gérer les erreurs
                        if MessageService._is_permission_error(error):
                            # Exclure ce groupe définitivement
                            failed_groups.add(group_id)
                            skipped += 1
                            logger.warning(f"Groupe {group_id} exclu: {error}")
                        elif MessageService._is_flood_error(error):
                            # Attendre le temps demandé par Telegram
                            wait_time = MessageService._extract_wait_time(error)
                            logger.warning(f"Flood limit détecté: attente de {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            
                            # Mettre à jour les timers pour le délai respecté
                            current_time = asyncio.get_event_loop().time()
                            last_send_time[group_id] = current_time
                            last_global_send = current_time
                            
                            # Réessayer UNE SEULE fois
                            success, retry_error = await account.schedule_message(
                                group_id,
                                message,
                                dt,
                                file_path
                            )
                            
                            # Enregistrer à nouveau l'heure après le réessai
                            current_time = asyncio.get_event_loop().time()
                            last_send_time[group_id] = current_time
                            last_global_send = current_time
                            
                            if success:
                                sent += 1
                                logger.info(f"✓ Réessai réussi pour groupe {group_id}")
                            else:
                                # Si ça échoue encore, exclure
                                failed_groups.add(group_id)
                                skipped += 1
                                logger.error(f"Réessai échoué pour groupe {group_id}: {retry_error}")
                        else:
                            # Autre erreur : pas de réessai
                            failed_groups.add(group_id)
                            skipped += 1
                        
                        if on_progress:
                            on_progress(sent, total, skipped, failed_groups)
                    
                except Exception as e:
                    logger.error(f"Erreur inattendue pour groupe {group_id}: {e}")
                    failed_groups.add(group_id)
                    skipped += 1
                    
                    if on_progress:
                        on_progress(sent, total, skipped, failed_groups)
        
        logger.info(f"Envoi terminé: {sent} envoyés, {skipped} skipped, {len(failed_groups)} groupes en erreur")
        return sent, skipped, failed_groups
    
    @staticmethod
    def _is_permission_error(error: str) -> bool:
        """Vérifie si c'est une erreur de permission."""
        error_lower = error.lower()
        return any(x in error_lower for x in [
            "can't write",
            "topic_closed",
            "chat_write_forbidden",
            "permission"
        ])
    
    @staticmethod
    def _is_flood_error(error: str) -> bool:
        """Vérifie si c'est une erreur de flood limit."""
        return 'wait' in error.lower() and 'seconds' in error.lower()
    
    @staticmethod
    def _extract_wait_time(error: str) -> int:
        """Extrait le temps d'attente d'une erreur de flood."""
        import re
        match = re.search(r'(\d+)\s*seconds', error.lower())
        if match:
            return int(match.group(1)) + 5  # Ajouter 5s de marge
        return 60  # Valeur par défaut
    
    @staticmethod
    def cleanup_temp_file(file_path: Optional[str]) -> None:
        """
        Nettoie un fichier temporaire.
        
        Args:
            file_path: Chemin du fichier à supprimer
        """
        if not file_path:
            return
        
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Fichier temporaire nettoyé: {file_path}")
        except Exception as e:
            logger.error(f"Erreur nettoyage fichier temporaire: {e}")

