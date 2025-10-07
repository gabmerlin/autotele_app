"""
Tests pour le gestionnaire de licences
"""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.license_manager import LicenseManager


class TestLicenseManager:
    """Tests pour LicenseManager"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Créer un répertoire de config temporaire"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Changer le répertoire de config
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            os.makedirs("config", exist_ok=True)
            yield tmpdir
            os.chdir(original_dir)
    
    def test_init(self, temp_config_dir):
        """Test d'initialisation"""
        manager = LicenseManager()
        
        assert manager is not None
        assert manager.license_data is not None
        assert "status" in manager.license_data
    
    def test_trial_active_initially(self, temp_config_dir):
        """Test que la période d'essai est active initialement"""
        manager = LicenseManager()
        
        assert manager.is_trial_active()
        assert manager.license_data["status"] == "trial"
    
    def test_trial_days_remaining(self, temp_config_dir):
        """Test du calcul des jours d'essai restants"""
        manager = LicenseManager()
        
        status = manager.get_license_status()
        
        assert status["is_trial"]
        assert status["trial_days_left"] >= 0
        assert status["trial_days_left"] <= manager.trial_days
    
    def test_trial_expired(self, temp_config_dir):
        """Test de l'expiration de la période d'essai"""
        manager = LicenseManager()
        
        # Modifier la date de fin d'essai pour qu'elle soit dans le passé
        manager.license_data["trial_end"] = (
            datetime.now() - timedelta(days=1)
        ).isoformat()
        
        assert not manager.is_trial_active()
        assert not manager.is_license_valid()
    
    def test_activate_license(self, temp_config_dir):
        """Test d'activation d'une licence"""
        manager = LicenseManager()
        
        # Désactiver la vérification BTCPay pour les tests
        manager.btcpay_url = ""
        
        license_key = "test_license_key_1234567890abcdef"
        success, message = manager.activate_license(license_key)
        
        assert success
        assert manager.license_data["status"] == "active"
        assert manager.license_data["license_key"] == license_key
        assert manager.is_license_valid()
    
    def test_activate_short_license_fails(self, temp_config_dir):
        """Test qu'une clé trop courte échoue"""
        manager = LicenseManager()
        manager.btcpay_url = ""
        
        short_key = "short"
        success, message = manager.activate_license(short_key)
        
        assert not success
    
    def test_license_status_active(self, temp_config_dir):
        """Test du statut d'une licence active"""
        manager = LicenseManager()
        manager.btcpay_url = ""
        
        manager.activate_license("test_key_1234567890abcdef")
        
        status = manager.get_license_status()
        
        assert status["is_valid"]
        assert status["status"] == "active"
        assert not status["is_trial"]
    
    def test_license_expiry(self, temp_config_dir):
        """Test de l'expiration de licence"""
        manager = LicenseManager()
        
        # Activer une licence
        manager.license_data["status"] = "active"
        manager.license_data["license_key"] = "test_key"
        manager.license_data["expiry_date"] = (
            datetime.now() - timedelta(days=1)
        ).isoformat()
        
        assert not manager.is_license_valid()
    
    def test_deactivate_license(self, temp_config_dir):
        """Test de désactivation de licence"""
        manager = LicenseManager()
        manager.btcpay_url = ""
        
        # Activer d'abord
        manager.activate_license("test_key_1234567890abcdef")
        assert manager.is_license_valid()
        
        # Désactiver
        manager.deactivate_license()
        
        assert manager.license_data["status"] == "deactivated"
        assert manager.license_data["license_key"] == ""
    
    def test_machine_id_generation(self, temp_config_dir):
        """Test de génération de machine ID"""
        manager = LicenseManager()
        
        machine_id = manager._get_machine_id()
        
        assert machine_id is not None
        assert len(machine_id) == 16
        assert isinstance(machine_id, str)
        
        # Le même machine devrait toujours donner le même ID
        machine_id2 = manager._get_machine_id()
        assert machine_id == machine_id2
    
    def test_persistence(self, temp_config_dir):
        """Test de la persistance des données de licence"""
        manager1 = LicenseManager()
        manager1.btcpay_url = ""
        
        # Activer une licence
        license_key = "persistent_key_1234567890"
        manager1.activate_license(license_key)
        
        # Créer un nouveau gestionnaire (devrait charger la licence)
        manager2 = LicenseManager()
        
        assert manager2.license_data["license_key"] == license_key
        assert manager2.license_data["status"] == "active"
        assert manager2.is_license_valid()
    
    def test_create_payment_invoice_no_btcpay(self, temp_config_dir):
        """Test de création de facture sans BTCPay configuré"""
        manager = LicenseManager()
        
        # Pas de BTCPay configuré
        manager.btcpay_url = ""
        manager.api_key = ""
        
        success, url, order_id = manager.create_payment_invoice()
        
        assert not success
        assert url == ""
        assert order_id == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

