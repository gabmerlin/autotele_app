"""
Tests pour le scheduler de messages
"""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.scheduler import ScheduledTask, MessageScheduler


class TestScheduledTask:
    """Tests pour ScheduledTask"""
    
    def test_create_task(self):
        """Test de création d'une tâche"""
        task = ScheduledTask(
            task_id="test_123",
            session_id="session_abc",
            account_name="Test Account",
            groups=[{"id": 1, "title": "Group 1"}],
            message="Test message",
            schedule_time=datetime.now() + timedelta(hours=1)
        )
        
        assert task.task_id == "test_123"
        assert task.session_id == "session_abc"
        assert task.account_name == "Test Account"
        assert len(task.groups) == 1
        assert task.message == "Test message"
        assert task.status == "pending"
    
    def test_task_to_dict(self):
        """Test de sérialisation en dictionnaire"""
        schedule_time = datetime.now() + timedelta(hours=1)
        task = ScheduledTask(
            task_id="test_123",
            session_id="session_abc",
            account_name="Test Account",
            groups=[{"id": 1, "title": "Group 1"}],
            message="Test message",
            schedule_time=schedule_time
        )
        
        data = task.to_dict()
        
        assert data["task_id"] == "test_123"
        assert data["session_id"] == "session_abc"
        assert data["status"] == "pending"
        assert isinstance(data["schedule_time"], str)
    
    def test_task_from_dict(self):
        """Test de désérialisation depuis un dictionnaire"""
        schedule_time = datetime.now() + timedelta(hours=1)
        data = {
            "task_id": "test_123",
            "session_id": "session_abc",
            "account_name": "Test Account",
            "groups": [{"id": 1, "title": "Group 1"}],
            "message": "Test message",
            "schedule_time": schedule_time.isoformat(),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "results": {}
        }
        
        task = ScheduledTask.from_dict(data)
        
        assert task.task_id == "test_123"
        assert task.status == "pending"
        assert isinstance(task.schedule_time, datetime)


class MockTelegramManager:
    """Mock pour TelegramManager"""
    
    def __init__(self):
        self.accounts = {}
    
    def get_account(self, session_id):
        return self.accounts.get(session_id)


class MockTelegramAccount:
    """Mock pour TelegramAccount"""
    
    def __init__(self):
        self.is_connected = True
        self.schedule_results = []
    
    async def schedule_message(self, chat_id, message, schedule_time, file_path=None):
        """Mock de planification de message"""
        self.schedule_results.append({
            "chat_id": chat_id,
            "message": message,
            "schedule_time": schedule_time
        })
        return True, ""


class TestMessageScheduler:
    """Tests pour MessageScheduler"""
    
    def test_create_scheduler(self):
        """Test de création du scheduler"""
        telegram_manager = MockTelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        assert scheduler is not None
        assert scheduler.telegram_manager == telegram_manager
        assert isinstance(scheduler.tasks, dict)
    
    def test_create_task(self):
        """Test de création d'une tâche"""
        telegram_manager = MockTelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        schedule_time = datetime.now() + timedelta(hours=1)
        task_id = scheduler.create_task(
            session_id="session_123",
            account_name="Test Account",
            groups=[{"id": 1, "title": "Group 1"}],
            message="Test message",
            schedule_time=schedule_time
        )
        
        assert task_id is not None
        assert task_id in scheduler.tasks
        
        task = scheduler.tasks[task_id]
        assert task.status == "pending"
        assert task.message == "Test message"
    
    def test_create_task_past_time_fails(self):
        """Test que créer une tâche dans le passé échoue"""
        telegram_manager = MockTelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        past_time = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(ValueError, match="dans le futur"):
            scheduler.create_task(
                session_id="session_123",
                account_name="Test Account",
                groups=[{"id": 1, "title": "Group 1"}],
                message="Test message",
                schedule_time=past_time
            )
    
    def test_get_task(self):
        """Test de récupération d'une tâche"""
        telegram_manager = MockTelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        schedule_time = datetime.now() + timedelta(hours=1)
        task_id = scheduler.create_task(
            session_id="session_123",
            account_name="Test Account",
            groups=[{"id": 1, "title": "Group 1"}],
            message="Test message",
            schedule_time=schedule_time
        )
        
        task = scheduler.get_task(task_id)
        assert task is not None
        assert task.task_id == task_id
    
    def test_list_tasks(self):
        """Test de listage des tâches"""
        telegram_manager = MockTelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        # Créer plusieurs tâches
        for i in range(3):
            scheduler.create_task(
                session_id=f"session_{i}",
                account_name=f"Account {i}",
                groups=[{"id": i, "title": f"Group {i}"}],
                message=f"Message {i}",
                schedule_time=datetime.now() + timedelta(hours=i+1)
            )
        
        tasks = scheduler.list_tasks()
        assert len(tasks) == 3
    
    def test_list_tasks_by_status(self):
        """Test de filtrage des tâches par statut"""
        telegram_manager = MockTelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        # Créer des tâches
        task_id1 = scheduler.create_task(
            session_id="session_1",
            account_name="Account 1",
            groups=[{"id": 1, "title": "Group 1"}],
            message="Message 1",
            schedule_time=datetime.now() + timedelta(hours=1)
        )
        
        task_id2 = scheduler.create_task(
            session_id="session_2",
            account_name="Account 2",
            groups=[{"id": 2, "title": "Group 2"}],
            message="Message 2",
            schedule_time=datetime.now() + timedelta(hours=2)
        )
        
        # Modifier le statut d'une tâche
        scheduler.tasks[task_id1].status = "completed"
        
        pending_tasks = scheduler.list_tasks(status="pending")
        completed_tasks = scheduler.list_tasks(status="completed")
        
        assert len(pending_tasks) == 1
        assert len(completed_tasks) == 1
        assert pending_tasks[0].task_id == task_id2
        assert completed_tasks[0].task_id == task_id1
    
    def test_delete_task(self):
        """Test de suppression d'une tâche"""
        telegram_manager = MockTelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        task_id = scheduler.create_task(
            session_id="session_123",
            account_name="Test Account",
            groups=[{"id": 1, "title": "Group 1"}],
            message="Test message",
            schedule_time=datetime.now() + timedelta(hours=1)
        )
        
        assert task_id in scheduler.tasks
        
        scheduler.delete_task(task_id)
        
        assert task_id not in scheduler.tasks
    
    def test_get_statistics(self):
        """Test de récupération des statistiques"""
        telegram_manager = MockTelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        # Créer des tâches avec différents statuts
        task_ids = []
        for i in range(5):
            task_id = scheduler.create_task(
                session_id=f"session_{i}",
                account_name=f"Account {i}",
                groups=[{"id": i, "title": f"Group {i}"}],
                message=f"Message {i}",
                schedule_time=datetime.now() + timedelta(hours=i+1)
            )
            task_ids.append(task_id)
        
        # Modifier les statuts
        scheduler.tasks[task_ids[0]].status = "completed"
        scheduler.tasks[task_ids[1]].status = "completed"
        scheduler.tasks[task_ids[2]].status = "failed"
        # task_ids[3] et [4] restent "pending"
        
        stats = scheduler.get_statistics()
        
        assert stats["total"] == 5
        assert stats["pending"] == 2
        assert stats["completed"] == 2
        assert stats["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_check_pending_tasks(self):
        """Test de vérification des tâches en attente"""
        telegram_manager = MockTelegramManager()
        
        # Ajouter un compte mock
        mock_account = MockTelegramAccount()
        telegram_manager.accounts["session_123"] = mock_account
        
        scheduler = MessageScheduler(telegram_manager)
        
        # Créer une tâche qui devrait être exécutée (dans le passé)
        past_time = datetime.now() - timedelta(seconds=1)
        
        # Créer la tâche manuellement pour contourner la validation
        from core.scheduler import ScheduledTask
        task = ScheduledTask(
            task_id="test_past",
            session_id="session_123",
            account_name="Test Account",
            groups=[{"id": 1, "title": "Group 1"}],
            message="Past message",
            schedule_time=past_time
        )
        scheduler.tasks["test_past"] = task
        
        # Vérifier les tâches
        await scheduler.check_pending_tasks()
        
        # La tâche devrait être traitée
        assert task.status in ["processing", "completed", "partial"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

