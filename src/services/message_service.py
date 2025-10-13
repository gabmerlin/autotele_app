"""Service de gestion des messages programmés avec rate limiting global."""
import asyncio
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from core.telegram.account import TelegramAccount
from utils.constants import (
    TELEGRAM_GLOBAL_RATE_LIMIT,
    TELEGRAM_SAFETY_MARGIN
)
from utils.logger import get_logger

logger = get_logger()


class GlobalRateLimiter:
    """
    Rate limiter global adaptatif avec attente non-bloquante.

    S'adapte automatiquement après un FloodWait pour éviter les répétitions.
    """

    def __init__(self):
        """Initialise le rate limiter global."""
        self._lock = None
        self._active_accounts = set()
        self._last_request_time = 0.0

        # Limite globale fixe
        self._global_rate_limit = (
            TELEGRAM_GLOBAL_RATE_LIMIT * TELEGRAM_SAFETY_MARGIN
        )
        self._min_delay = 1.0 / self._global_rate_limit

        # Système adaptatif par compte
        self._account_flood_counts: Dict[str, int] = {}
        self._account_penalty_multipliers: Dict[str, float] = {}
        self._account_successful_since_flood: Dict[str, int] = {}
        self._recovery_threshold = 50
    
    def _get_lock(self):
        """Crée ou récupère le lock global."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    def register_account(self, account_id: str) -> None:
        """Enregistre un compte comme actif et initialise ses compteurs."""
        self._active_accounts.add(account_id)

        # Initialiser les compteurs adaptatifs pour ce compte
        if account_id not in self._account_flood_counts:
            self._account_flood_counts[account_id] = 0
            self._account_penalty_multipliers[account_id] = 1.0
            self._account_successful_since_flood[account_id] = 0

    def unregister_account(self, account_id: str) -> None:
        """Désenregistre un compte actif."""
        self._active_accounts.discard(account_id)
    
    def report_flood(self, account_id: str) -> None:
        """
        Signale qu'un FloodWait a été détecté pour ce compte.

        Ralentit automatiquement le débit pour éviter les répétitions.
        """
        self._account_flood_counts[account_id] = (
            self._account_flood_counts.get(account_id, 0) + 1
        )
        old_penalty = self._account_penalty_multipliers.get(account_id, 1.0)

        # Augmenter la pénalité : multiplier par 1.5 à chaque flood (max 4.0)
        new_penalty = min(old_penalty * 1.5, 4.0)
        self._account_penalty_multipliers[account_id] = new_penalty
        self._account_successful_since_flood[account_id] = 0

        new_rate = self._global_rate_limit / new_penalty
        logger.warning(
            f"FloodWait #{self._account_flood_counts[account_id]} détecté → "
            f"Débit réduit: {new_rate:.1f} req/s "
            f"(pénalité ×{new_penalty:.1f})"
        )

    def report_success(self, account_id: str) -> None:
        """Signale un envoi réussi et récupère progressivement le débit."""
        if account_id not in self._account_successful_since_flood:
            return

        self._account_successful_since_flood[account_id] += 1
        successes = self._account_successful_since_flood[account_id]
        penalty = self._account_penalty_multipliers.get(account_id, 1.0)

        # Récupération progressive : tous les 50 succès, réduire de 20%
        if successes >= self._recovery_threshold and penalty > 1.0:
            new_penalty = max(penalty * 0.8, 1.0)
            self._account_penalty_multipliers[account_id] = new_penalty
            self._account_successful_since_flood[account_id] = 0
            
    
    async def _calculate_wait_time(self, account_id: str) -> float:
        """
        Calcule le temps d'attente avec pénalité adaptative (thread-safe).
        """
        async with self._get_lock():
            penalty = self._account_penalty_multipliers.get(account_id, 1.0)
            adjusted_delay = self._min_delay * penalty

            now = time.time()
            if self._last_request_time > 0:
                elapsed = now - self._last_request_time
                if elapsed < adjusted_delay:
                    return adjusted_delay - elapsed
            return 0.0

    @asynccontextmanager
    async def request_slot(self, account_id: str):
        """
        Context manager pour acquérir un slot de requête.

        Les attentes se font EN DEHORS du lock pour ne pas bloquer les
        autres comptes.

        Usage:
            async with rate_limiter.request_slot(account_id):
                await account.schedule_message(...)
        """
        # Calculer et attendre EN DEHORS du lock (avec pénalité adaptative)
        wait_time = await self._calculate_wait_time(account_id)
        if wait_time > 0:
            await asyncio.sleep(wait_time)

        # Lock très court juste pour marquer le slot
        async with self._get_lock():
            self._last_request_time = time.time()

        # L'envoi se fait en parallèle avec les autres comptes
        yield


# Instance globale
_rate_limiter = GlobalRateLimiter()


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
        cancelled_flag: Optional[Dict] = None,
        task: Optional['SendingTask'] = None
    ) -> Tuple[int, int, Set[int]]:
        """
        Envoie des messages programmés avec rate limiting global strict.
        
        Args:
            account: Compte Telegram à utiliser
            group_ids: Liste des IDs de groupes
            message: Message à envoyer
            dates: Liste des dates de planification
            file_path: Chemin du fichier à joindre (optionnel)
            on_progress: Callback pour suivre la progression
            cancelled_flag: Dict avec une clé 'value' pour annuler l'envoi
            task: Tâche d'envoi (optionnel, pour afficher les attentes FloodWait)
            
        Returns:
            Tuple[int, int, Set[int]]: (nb_envoyés, nb_skipped, groupes_en_erreur)
        """
        if not account.is_connected:
            raise ValueError("Le compte n'est pas connecté")
        
        account_id = account.session_id
        _rate_limiter.register_account(account_id)
        
        # Démarrer le chronomètre pour les métriques de performance
        start_time = time.time()
        
        try:
            total_groups = len(group_ids)
            total_dates = len(dates)
            initial_total = total_groups * total_dates
            total = initial_total
            sent = 0
            skipped = 0
            failed_groups: Set[int] = set()
            
            # Pré-remplir le cache d'entités pour éviter les cache miss pendant l'envoi
            cache_filled = 0
            for group_id in group_ids:
                if group_id not in account._entity_cache:
                    try:
                        entity = await account.client.get_input_entity(group_id)
                        account._entity_cache[group_id] = entity
                        cache_filled += 1
                        # Petit délai pour ne pas surcharger l'API
                        if cache_filled % 10 == 0:
                            await asyncio.sleep(0.1)
                    except Exception as e:
                        pass
            
            # Upload du fichier UNE SEULE FOIS si nécessaire
            uploaded_file = None
            if file_path and Path(file_path).exists():
                try:
                    async with _rate_limiter.request_slot(account_id):
                        import mimetypes
                        from telethon.tl.types import (
                            InputMediaUploadedDocument, 
                            DocumentAttributeFilename
                        )
                        
                        # Upload du fichier
                        file_input = await account.client.upload_file(file_path)
                        
                        # Déterminer le type MIME
                        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                        
                        # Créer les attributs (nom du fichier)
                        file_name = Path(file_path).name
                        attributes = [DocumentAttributeFilename(file_name=file_name)]
                        
                        # Créer le média uploadé correctement
                        uploaded_file = InputMediaUploadedDocument(
                            file=file_input,
                            mime_type=mime_type,
                            attributes=attributes
                        )
                except Exception as e:
                    logger.warning(f"Échec upload: {e}")
                    uploaded_file = None
            
            # Créer toutes les paires (date, groupe) et les randomiser
            # Cela évite la détection de pattern de spam par Telegram
            schedule_pairs = [(dt, group_id) for dt in dates for group_id in group_ids]
            random.shuffle(schedule_pairs)
            
            # Parcourir les paires dans l'ordre randomisé
            for idx, (dt, group_id) in enumerate(schedule_pairs, 1):
                if cancelled_flag and cancelled_flag.get('value'):
                    break
                
                # Skip les groupes qui ont déjà échoué
                if group_id in failed_groups:
                    skipped += 1
                    if on_progress:
                        on_progress(sent, total, skipped, failed_groups)
                    continue
                
                try:
                    # Acquérir le slot et envoyer (atomique)
                    async with _rate_limiter.request_slot(account_id):
                        # Si fichier uploadé, l'utiliser ; sinon utiliser le chemin direct
                        success, error = await account.schedule_message(
                            group_id,
                            message,
                            dt,
                            file_path=None if uploaded_file else file_path,
                            uploaded_file=uploaded_file
                        )
                    # Le timestamp est automatiquement enregistré à la sortie du context manager
                    
                    if success:
                        sent += 1
                        # Signaler le succès pour récupération adaptative
                        _rate_limiter.report_success(account_id)
                        if on_progress:
                            on_progress(sent, total, skipped, failed_groups)
                    else:
                        # Gérer les erreurs
                        if MessageService._is_permission_error(error):
                            if group_id not in failed_groups:
                                failed_groups.add(group_id)
                                # Calculer combien de messages restants pour ce groupe
                                remaining_for_group = sum(1 for _, gid in schedule_pairs[idx:] if gid == group_id)
                                total -= remaining_for_group
                                logger.warning(
                                    f"Groupe {group_id} exclu: {error} ({remaining_for_group} msg restants retirés)"
                                )
                            skipped += 1
                        elif MessageService._is_flood_error(error):
                            # Signaler le flood pour ajustement adaptatif
                            _rate_limiter.report_flood(account_id)
                            
                            # Flood: attendre et réessayer
                            wait_time = MessageService._extract_wait_time(error)
                            logger.warning(f"Flood: attente {wait_time}s...")
                            
                            # Signaler l'attente à la tâche (pour affichage UI)
                            if task:
                                task.set_waiting(wait_time + 2)  # +2s marge de sécurité
                            
                            await asyncio.sleep(wait_time)
                            
                            # Réessayer avec marge de sécurité supplémentaire
                            await asyncio.sleep(2.0)  # +2s de sécurité
                            
                            # Effacer l'attente (reprise)
                            if task:
                                task.clear_waiting()
                            
                            async with _rate_limiter.request_slot(account_id):
                                success, retry_error = await account.schedule_message(
                                    group_id, message, dt, 
                                    file_path=None if uploaded_file else file_path,
                                    uploaded_file=uploaded_file
                                )
                            
                            if success:
                                sent += 1
                                _rate_limiter.report_success(account_id)
                            else:
                                failed_groups.add(group_id)
                                skipped += 1
                                logger.error(f"Réessai échoué: {retry_error}")
                        else:
                            failed_groups.add(group_id)
                            skipped += 1
                        
                        if on_progress:
                            on_progress(sent, total, skipped, failed_groups)
                    
                except Exception as e:
                    logger.error(f"Erreur inattendue {group_id}: {e}")
                    failed_groups.add(group_id)
                    skipped += 1
                    if on_progress:
                        on_progress(sent, total, skipped, failed_groups)
            
            # Calculer les métriques de performance
            elapsed_time = time.time() - start_time
            messages_per_second = sent / elapsed_time if elapsed_time > 0 else 0
            success_rate = (sent / initial_total * 100) if initial_total > 0 else 0
            
            return sent, skipped, failed_groups
            
        finally:
            _rate_limiter.unregister_account(account_id)
    
    @staticmethod
    def _is_permission_error(error: str) -> bool:
        """Vérifie si c'est une erreur de permission."""
        error_lower = error.lower()
        return any(x in error_lower for x in [
            "can't write", "topic_closed", "chat_write_forbidden", "permission"
        ])
    
    @staticmethod
    def _is_flood_error(error: str) -> bool:
        """Vérifie si c'est une erreur de flood limit (français et anglais)."""
        error_lower = error.lower()
        # Détection anglais : "wait X seconds"
        english_flood = 'wait' in error_lower and 'seconds' in error_lower
        # Détection français : "attendez X secondes" ou "rate limit"
        french_flood = 'attendez' in error_lower and 'secondes' in error_lower
        rate_limit = 'rate limit' in error_lower
        
        return english_flood or french_flood or rate_limit
    
    @staticmethod
    def _extract_wait_time(error: str) -> int:
        """Extrait le temps d'attente d'une erreur de flood (français et anglais)."""
        import re
        error_lower = error.lower()
        
        # Chercher en anglais : "wait 236 seconds"
        match = re.search(r'wait\s+(\d+)\s*seconds?', error_lower)
        if match:
            return int(match.group(1)) + 5
        
        # Chercher format alternatif anglais : "236 seconds"
        match = re.search(r'(\d+)\s*seconds?', error_lower)
        if match:
            return int(match.group(1)) + 5
        
        # Chercher en français : "attendez 236 secondes"
        match = re.search(r'attendez\s+(\d+)\s*secondes?', error_lower)
        if match:
            return int(match.group(1)) + 5
        
        # Si rien trouvé, défaut à 60 secondes
        return 60
    
    @staticmethod
    def cleanup_temp_file(file_path: Optional[str]) -> None:
        """Nettoie un fichier temporaire."""
        if not file_path:
            return
        
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
        except Exception as e:
            logger.error(f"Erreur nettoyage fichier: {e}")
