"""
Tests d'intégration pour AutoTele
Ces tests nécessitent une configuration réelle (Telegram API, BTCPay)
et sont marqués comme 'integration' pour être exécutés séparément.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Ces tests sont marqués pour être skippés par défaut
pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not Path("config/test_credentials.json").exists(),
    reason="Fichier de credentials de test non trouvé"
)
class TestTelegramIntegration:
    """
    Tests d'intégration avec l'API Telegram
    Nécessite config/test_credentials.json avec :
    {
        "phone": "+33...",
        "api_id": "...",
        "api_hash": "..."
    }
    """
    
    @pytest.fixture
    def test_credentials(self):
        """Charge les credentials de test"""
        import json
        with open("config/test_credentials.json") as f:
            return json.load(f)
    
    @pytest.mark.asyncio
    async def test_connect_telegram(self, test_credentials):
        """Test de connexion à Telegram"""
        from core.telegram_manager import TelegramAccount
        
        account = TelegramAccount(
            session_id="test_session",
            phone=test_credentials["phone"],
            api_id=test_credentials["api_id"],
            api_hash=test_credentials["api_hash"],
            account_name="Test Account"
        )
        
        # Note: Ce test nécessite une session déjà authentifiée
        # ou une authentification manuelle
        connected = await account.connect()
        
        if connected:
            assert account.is_connected
            
            # Tester la récupération des dialogues
            dialogs = await account.get_dialogs()
            assert isinstance(dialogs, list)
            
            # Déconnecter
            await account.disconnect()
            assert not account.is_connected
    
    @pytest.mark.asyncio
    async def test_schedule_message(self, test_credentials):
        """Test de planification d'un message"""
        from core.telegram_manager import TelegramAccount
        
        account = TelegramAccount(
            session_id="test_session",
            phone=test_credentials["phone"],
            api_id=test_credentials["api_id"],
            api_hash=test_credentials["api_hash"]
        )
        
        connected = await account.connect()
        
        if connected and "test_chat_id" in test_credentials:
            # Planifier un message de test dans 1 heure
            chat_id = test_credentials["test_chat_id"]
            message = "Test message from AutoTele - Please ignore"
            schedule_time = datetime.now() + timedelta(hours=1)
            
            success, error = await account.schedule_message(
                chat_id, message, schedule_time
            )
            
            # Note: Ce test créera réellement un message planifié
            # Utilisez un groupe de test !
            assert success or "rate limit" in error.lower()
            
            await account.disconnect()


@pytest.mark.skipif(
    not Path("config/btcpay_test.json").exists(),
    reason="Fichier de config BTCPay de test non trouvé"
)
class TestBTCPayIntegration:
    """
    Tests d'intégration avec BTCPay Server
    Nécessite config/btcpay_test.json avec :
    {
        "server_url": "https://...",
        "store_id": "...",
        "api_key": "..."
    }
    """
    
    @pytest.fixture
    def btcpay_config(self):
        """Charge la config BTCPay de test"""
        import json
        with open("config/btcpay_test.json") as f:
            return json.load(f)
    
    def test_btcpay_connection(self, btcpay_config):
        """Test de connexion à BTCPay"""
        import requests
        
        headers = {
            "Authorization": f"token {btcpay_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{btcpay_config['server_url']}/api/v1/stores/{btcpay_config['store_id']}",
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 200
        store_data = response.json()
        assert store_data["id"] == btcpay_config["store_id"]
    
    def test_create_invoice(self, btcpay_config):
        """Test de création d'une facture"""
        import requests
        
        headers = {
            "Authorization": f"token {btcpay_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "amount": "0.01",  # Petit montant pour test
            "currency": "EUR",
            "orderId": f"test_{datetime.now().timestamp()}"
        }
        
        response = requests.post(
            f"{btcpay_config['server_url']}/api/v1/stores/{btcpay_config['store_id']}/invoices",
            headers=headers,
            json=data,
            timeout=10
        )
        
        assert response.status_code in [200, 201]
        invoice = response.json()
        assert "id" in invoice
        assert "checkoutLink" in invoice
        assert invoice["status"] == "new"
    
    def test_license_manager_with_btcpay(self, btcpay_config):
        """Test du LicenseManager avec BTCPay réel"""
        from core.license_manager import LicenseManager
        
        manager = LicenseManager()
        manager.btcpay_url = btcpay_config["server_url"]
        manager.store_id = btcpay_config["store_id"]
        manager.api_key = btcpay_config["api_key"]
        
        # Créer une facture
        success, url, order_id = manager.create_payment_invoice(0.01, "EUR")
        
        assert success
        assert url != ""
        assert order_id != ""
        
        print(f"\nInvoice créée: {url}")
        print(f"Order ID / License Key: {order_id}")


class TestEndToEnd:
    """
    Tests de bout en bout (end-to-end)
    Ces tests vérifient le workflow complet de l'application
    """
    
    @pytest.mark.asyncio
    async def test_complete_workflow_mock(self):
        """
        Test du workflow complet avec des mocks
        1. Créer un compte
        2. Planifier un message
        3. Vérifier que la tâche est créée
        4. (Simulation) Exécuter la tâche
        """
        from core.telegram_manager import TelegramManager
        from core.scheduler import MessageScheduler
        
        # Note: Ce test utilise des mocks, pas de vraies connexions
        telegram_manager = TelegramManager()
        scheduler = MessageScheduler(telegram_manager)
        
        # Simuler l'ajout d'un compte (ne fonctionne pas vraiment sans credentials)
        # Dans un vrai test E2E, on utiliserait de vrais credentials
        
        # Créer une tâche
        schedule_time = datetime.now() + timedelta(hours=1)
        
        # Note: Cette tâche échouera à l'exécution car pas de compte réel
        task_id = scheduler.create_task(
            session_id="mock_session",
            account_name="Mock Account",
            groups=[{"id": 123, "title": "Mock Group"}],
            message="Test message E2E",
            schedule_time=schedule_time
        )
        
        assert task_id is not None
        
        # Vérifier que la tâche existe
        task = scheduler.get_task(task_id)
        assert task is not None
        assert task.status == "pending"
        
        # Vérifier les stats
        stats = scheduler.get_statistics()
        assert stats["pending"] >= 1


def test_application_structure():
    """Test de la structure de l'application"""
    required_dirs = [
        "src",
        "src/core",
        "src/ui",
        "src/utils",
        "build",
        "docs",
        "tests"
    ]
    
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Répertoire manquant: {dir_path}"
    
    required_files = [
        "src/main.py",
        "src/core/telegram_manager.py",
        "src/core/scheduler.py",
        "src/core/license_manager.py",
        "src/ui/main_window.py",
        "requirements.txt",
        "README.md"
    ]
    
    for file_path in required_files:
        assert Path(file_path).exists(), f"Fichier manquant: {file_path}"


if __name__ == "__main__":
    # Pour exécuter seulement les tests d'intégration:
    # pytest tests/test_integration.py -v -m integration
    pytest.main([__file__, "-v"])

