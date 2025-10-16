"""
Gestionnaire des tâches d'envoi en arrière-plan.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field

from utils.logger import get_logger

logger = get_logger()


@dataclass
class SendingTask:
    """Représente une tâche d'envoi en cours."""
    task_id: str
    account_session_id: str
    account_name: str
    group_count: int
    date_count: int
    total_messages: int
    sent: int = 0
    skipped: int = 0
    failed_groups: Set[int] = field(default_factory=set)
    status: str = "en_cours"  # en_cours, terminé, annulé
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    cancel_flag: Dict = field(default_factory=lambda: {'value': False})
    on_progress_callbacks: List[Callable] = field(default_factory=list)
    waiting_until: Optional[datetime] = None  # Heure de reprise après FloodWait
    
    @property
    def progress_percent(self) -> float:
        """Calcule le pourcentage de progression."""
        if self.total_messages == 0:
            return 0.0
        return (self.sent / self.total_messages) * 100
    
    @property
    def is_running(self) -> bool:
        """Vérifie si la tâche est en cours."""
        return self.status == "en_cours"
    
    @property
    def is_waiting(self) -> bool:
        """Vérifie si la tâche est en attente (FloodWait)."""
        return self.waiting_until is not None and self.waiting_until > datetime.now()
    
    def set_waiting(self, wait_seconds: int) -> None:
        """
        Définit une période d'attente (FloodWait).
        
        Args:
            wait_seconds: Nombre de secondes à attendre
        """
        from datetime import timedelta
        self.waiting_until = datetime.now() + timedelta(seconds=wait_seconds)
    
    def clear_waiting(self) -> None:
        """Efface la période d'attente."""
        self.waiting_until = None
    
    def cancel(self) -> None:
        """Annule la tâche."""
        self.cancel_flag['value'] = True
        self.status = "annulé"
    
    def complete(self) -> None:
        """Marque la tâche comme terminée."""
        self.status = "terminé"
        self.finished_at = datetime.now()
    
    def update_progress(self, sent: int, skipped: int, failed_groups: Set[int], total_adjusted: Optional[int] = None) -> None:
        """
        Met à jour la progression.
        
        Args:
            sent: Nombre de messages envoyés
            skipped: Nombre de messages ignorés
            failed_groups: Set des groupes en erreur
            total_adjusted: Total ajusté après exclusions (optionnel)
        """
        self.sent = sent
        self.skipped = skipped
        self.failed_groups = failed_groups
        
        # Mettre à jour le total si fourni (après exclusions)
        if total_adjusted is not None:
            self.total_messages = total_adjusted
        
        # Notifier les callbacks
        for callback in self.on_progress_callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Erreur callback progression: {e}")


class SendingTasksManager:
    """Gestionnaire global des tâches d'envoi."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialise le gestionnaire."""
        if self._initialized:
            return
        
        self.tasks: Dict[str, SendingTask] = {}
        self._initialized = True
    
    def create_task(
        self,
        account_session_id: str,
        account_name: str,
        group_count: int,
        date_count: int,
        total_messages: int
    ) -> SendingTask:
        """
        Crée une nouvelle tâche d'envoi.
        
        Args:
            account_session_id: ID de session du compte
            account_name: Nom du compte
            group_count: Nombre de groupes
            date_count: Nombre de dates
            total_messages: Nombre total de messages à envoyer
            
        Returns:
            SendingTask: La tâche créée
        """
        task_id = f"{account_session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = SendingTask(
            task_id=task_id,
            account_session_id=account_session_id,
            account_name=account_name,
            group_count=group_count,
            date_count=date_count,
            total_messages=total_messages
        )
        
        self.tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[SendingTask]:
        """Récupère une tâche par son ID."""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[SendingTask]:
        """Récupère toutes les tâches."""
        return list(self.tasks.values())
    
    def get_active_tasks(self) -> List[SendingTask]:
        """Récupère les tâches en cours."""
        return [task for task in self.tasks.values() if task.is_running]
    
    def get_tasks_for_account(self, account_session_id: str) -> List[SendingTask]:
        """Récupère toutes les tâches d'un compte."""
        return [
            task for task in self.tasks.values()
            if task.account_session_id == account_session_id
        ]
    
    def is_account_busy(self, account_session_id: str) -> bool:
        """Vérifie si un compte a des envois en cours."""
        return any(
            task.is_running
            for task in self.tasks.values()
            if task.account_session_id == account_session_id
        )
    
    def cancel_task(self, task_id: str) -> bool:
        """Annule une tâche."""
        task = self.get_task(task_id)
        if task and task.is_running:
            task.cancel()
            return True
        return False
    
    def complete_task(self, task_id: str) -> None:
        """Marque une tâche comme terminée."""
        task = self.get_task(task_id)
        if task:
            task.complete()
    
    def remove_task(self, task_id: str) -> None:
        """Supprime une tâche."""
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24) -> None:
        """Nettoie les tâches terminées de plus de X heures."""
        now = datetime.now()
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status != "en_cours" and task.finished_at:
                age_hours = (now - task.finished_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            self.remove_task(task_id)


# Instance globale
sending_tasks_manager = SendingTasksManager()

