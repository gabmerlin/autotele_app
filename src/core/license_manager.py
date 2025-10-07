"""
Gestionnaire de licences et abonnements via BTCPay Server
"""
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import hashlib

from utils.logger import get_logger
from utils.config import get_config


class LicenseManager:
    """Gère les licences et l'intégration BTCPay Server"""
    
    def __init__(self):
        self.logger = get_logger()
        self.config = get_config()
        self.license_file = Path("config/license.json")
        self.license_data = self._load_license()
        
        # Configuration BTCPay
        self.btcpay_url = self.config.get("btcpay.server_url", "")
        self.store_id = self.config.get("btcpay.store_id", "")
        self.api_key = self.config.get("btcpay.api_key", "")
        self.trial_days = self.config.get("btcpay.trial_days", 7)
        
        # Vérification périodique
        self.last_check = None
        self.check_interval = timedelta(
            hours=self.config.get("btcpay.check_interval_hours", 24)
        )
    
    def _load_license(self) -> Dict:
        """Charge les données de licence"""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Erreur chargement licence: {e}")
        
        # Licence vide = période d'essai
        return {
            "license_key": "",
            "activation_date": None,
            "expiry_date": None,
            "status": "trial",
            "trial_start": datetime.now().isoformat(),
            "trial_end": (datetime.now() + timedelta(days=self.trial_days)).isoformat(),
            "machine_id": self._get_machine_id(),
            "last_verified": None
        }
    
    def _save_license(self):
        """Sauvegarde les données de licence"""
        try:
            self.license_file.parent.mkdir(exist_ok=True)
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(self.license_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde licence: {e}")
    
    def _get_machine_id(self) -> str:
        """Obtient un identifiant unique de la machine"""
        try:
            import subprocess
            result = subprocess.run(
                ['wmic', 'csproduct', 'get', 'uuid'],
                capture_output=True,
                text=True,
                check=True
            )
            uuid = result.stdout.split('\n')[1].strip()
            return hashlib.sha256(uuid.encode()).hexdigest()[:16]
        except Exception:
            import getpass
            import platform
            fallback = f"{platform.node()}-{getpass.getuser()}"
            return hashlib.sha256(fallback.encode()).hexdigest()[:16]
    
    def is_trial_active(self) -> bool:
        """Vérifie si la période d'essai est active"""
        if self.license_data.get("status") != "trial":
            return False
        
        trial_end = datetime.fromisoformat(self.license_data["trial_end"])
        return datetime.now() < trial_end
    
    def is_license_valid(self) -> bool:
        """Vérifie si la licence est valide"""
        # Période d'essai active
        if self.is_trial_active():
            return True
        
        # Licence activée
        if self.license_data.get("status") == "active":
            if self.license_data.get("expiry_date"):
                expiry = datetime.fromisoformat(self.license_data["expiry_date"])
                return datetime.now() < expiry
            # Pas de date d'expiration = licence permanente
            return True
        
        return False
    
    def get_license_status(self) -> Dict:
        """Récupère le statut détaillé de la licence"""
        status = {
            "is_valid": self.is_license_valid(),
            "status": self.license_data.get("status", "unknown"),
            "is_trial": self.license_data.get("status") == "trial",
        }
        
        if status["is_trial"]:
            trial_end = datetime.fromisoformat(self.license_data["trial_end"])
            days_left = (trial_end - datetime.now()).days
            status["trial_days_left"] = max(0, days_left)
            status["trial_end_date"] = trial_end.strftime("%Y-%m-%d")
        
        if self.license_data.get("expiry_date"):
            expiry = datetime.fromisoformat(self.license_data["expiry_date"])
            days_left = (expiry - datetime.now()).days
            status["expiry_days_left"] = max(0, days_left)
            status["expiry_date"] = expiry.strftime("%Y-%m-%d")
        
        return status
    
    def activate_license(self, license_key: str) -> Tuple[bool, str]:
        """
        Active une licence
        Retourne (success, message)
        """
        try:
            # Vérifier la clé auprès de BTCPay
            if not self._verify_license_with_btcpay(license_key):
                return False, "Clé de licence invalide"
            
            # Activer la licence
            self.license_data["license_key"] = license_key
            self.license_data["activation_date"] = datetime.now().isoformat()
            self.license_data["expiry_date"] = (
                datetime.now() + timedelta(days=30)
            ).isoformat()
            self.license_data["status"] = "active"
            self.license_data["last_verified"] = datetime.now().isoformat()
            
            self._save_license()
            self.logger.info(f"Licence activée: {license_key[:8]}...")
            
            return True, "Licence activée avec succès"
            
        except Exception as e:
            error_msg = f"Erreur activation licence: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _verify_license_with_btcpay(self, license_key: str) -> bool:
        """
        Vérifie une licence auprès de BTCPay Server
        """
        if not self.btcpay_url or not self.api_key:
            self.logger.warning("BTCPay non configuré, mode développement")
            # En mode dev, accepter toute clé de plus de 16 caractères
            return len(license_key) >= 16
        
        try:
            # Appel à l'API BTCPay pour vérifier la licence
            # NOTE: Ceci est un exemple, vous devrez adapter selon votre implementation BTCPay
            headers = {
                "Authorization": f"token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.btcpay_url}/api/v1/stores/{self.store_id}/invoices"
            
            # Chercher une facture correspondante
            params = {
                "orderId": license_key
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                invoices = response.json()
                if invoices:
                    invoice = invoices[0]
                    # Vérifier que la facture est payée
                    return invoice.get("status") == "settled"
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur vérification BTCPay: {e}")
            return False
    
    def check_license_validity(self) -> bool:
        """
        Vérifie périodiquement la validité de la licence
        Retourne True si valide, False sinon
        """
        # Ne vérifier que si l'intervalle est écoulé
        if self.last_check:
            if datetime.now() - self.last_check < self.check_interval:
                return self.is_license_valid()
        
        self.last_check = datetime.now()
        
        # Si en période d'essai, pas besoin de vérifier avec BTCPay
        if self.is_trial_active():
            return True
        
        # Vérifier la licence avec BTCPay
        license_key = self.license_data.get("license_key")
        if not license_key:
            return False
        
        is_valid = self._verify_license_with_btcpay(license_key)
        
        if is_valid:
            # Renouveler la date d'expiration
            self.license_data["expiry_date"] = (
                datetime.now() + timedelta(days=30)
            ).isoformat()
            self.license_data["last_verified"] = datetime.now().isoformat()
            self._save_license()
        else:
            # Licence expirée ou invalide
            self.license_data["status"] = "expired"
            self._save_license()
        
        self.logger.info(f"Vérification licence: {'valide' if is_valid else 'invalide'}")
        
        return is_valid
    
    def create_payment_invoice(self, amount: float = None, 
                              currency: str = None) -> Tuple[bool, str, str]:
        """
        Crée une facture de paiement sur BTCPay
        Retourne (success, invoice_url, order_id)
        """
        if not self.btcpay_url or not self.api_key:
            return False, "", ""
        
        try:
            amount = amount or self.config.get("btcpay.subscription_price", 29.99)
            currency = currency or self.config.get("btcpay.currency", "EUR")
            
            headers = {
                "Authorization": f"token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Générer un order_id unique qui servira de license_key
            from utils.crypto import generate_token
            order_id = generate_token(32)
            
            data = {
                "amount": str(amount),
                "currency": currency,
                "orderId": order_id,
                "metadata": {
                    "machineId": self.license_data["machine_id"],
                    "product": "AutoTele Subscription"
                },
                "checkout": {
                    "redirectURL": "https://votre-site.com/success",
                    "redirectAutomatically": False
                }
            }
            
            url = f"{self.btcpay_url}/api/v1/stores/{self.store_id}/invoices"
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                invoice_data = response.json()
                invoice_url = invoice_data.get("checkoutLink", "")
                
                self.logger.info(f"Facture créée: {order_id}")
                return True, invoice_url, order_id
            else:
                self.logger.error(f"Erreur création facture BTCPay: {response.status_code}")
                return False, "", ""
                
        except Exception as e:
            self.logger.error(f"Erreur création facture: {e}")
            return False, "", ""
    
    def deactivate_license(self):
        """Désactive la licence actuelle"""
        self.license_data["status"] = "deactivated"
        self.license_data["license_key"] = ""
        self._save_license()
        self.logger.info("Licence désactivée")

