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
                    # PROTECTION 1: Rate limit par chat (1 msg/sec/chat)
                    if group_id in last_send_time:
                        elapsed_chat = asyncio.get_event_loop().time() - last_send_time[group_id]
                        if elapsed_chat < TELEGRAM_MIN_DELAY_PER_CHAT:
                            wait_chat = TELEGRAM_MIN_DELAY_PER_CHAT - elapsed_chat
                            await asyncio.sleep(wait_chat)
                    
                    # PROTECTION 2: Rate limit global (25 msg/sec = 0.04s entre envois)
                    if last_global_send > 0:
                        elapsed_global = asyncio.get_event_loop().time() - last_global_send
                        if elapsed_global < TELEGRAM_MIN_DELAY_BETWEEN_MESSAGES:
                            wait_global = TELEGRAM_MIN_DELAY_BETWEEN_MESSAGES - elapsed_global
                            await asyncio.sleep(wait_global)
                    
                    # Envoyer le message
                    success, error = await account.schedule_message(
                        group_id,
                        message,
                        dt,
                        file_path
                    )
                    
                    if success:
                        sent += 1
                        
                        # Enregistrer l'heure d'envoi
                        current_time = asyncio.get_event_loop().time()
                        last_send_time[group_id] = current_time
                        last_global_send = current_time
                        
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
                            # Attendre et réessayer
                            wait_time = MessageService._extract_wait_time(error)
                            logger.warning(f"Flood limit: attente de {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            
                            # Réessayer
                            success, _ = await account.schedule_message(
                                group_id,
                                message,
                                dt,
                                file_path
                            )
                            
                            if success:
                                sent += 1
                                current_time = asyncio.get_event_loop().time()
                                last_send_time[group_id] = current_time
                                last_global_send = current_time
                            else:
                                # Si ça échoue encore, exclure
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

