"""
Service de gestion des abonnements et paiements BTCPay
"""
import asyncio
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import hmac
import json
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

from utils.logger import get_logger
from utils.config import Config

logger = get_logger()


class SubscriptionService:
    """Gère les abonnements et paiements via BTCPay Server et Supabase"""
    
    def __init__(self):
        self.config = Config()
        # SÉCURITÉ : Charger la config BTCPay depuis .env (pas depuis app_config.json)
        self.btcpay_config = self.config.get_btcpay_config()
        self.supabase: Optional[Client] = None
        self.current_subscription: Optional[Dict[str, Any]] = None
        self.auth_service = None  # Sera initialisé par get_authenticated_client
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialise la connexion Supabase"""
        try:
            # SÉCURITÉ : Charger la config depuis .env (pas depuis app_config.json)
            supabase_config = self.config.get_supabase_config()
            url = supabase_config.get('url', '')
            anon_key = supabase_config.get('anon_key', '')
            
            if not url or not anon_key:
                logger.warning("Configuration Supabase manquante pour le service d'abonnement")
                return
            
            if create_client is None:
                logger.error("Module supabase non disponible")
                return
            
            self.supabase = create_client(supabase_url=url, supabase_key=anon_key)
            logger.info("✅ Client Supabase initialisé (service abonnement)")
        except ValueError as e:
            # Erreur de configuration (secrets manquants dans .env)
            logger.error(f"❌ Configuration Supabase invalide: {e}")
            self.supabase = None
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Supabase: {e}")
    
    def _get_authenticated_client(self) -> Optional[Client]:
        """
        Retourne le client Supabase authentifié de auth_service
        pour que les politiques RLS fonctionnent correctement
        """
        try:
            # Import lazy pour éviter les imports circulaires
            if not self.auth_service:
                from services.auth_service import get_auth_service
                self.auth_service = get_auth_service()
            
            # Utiliser directement le client Supabase de auth_service
            # qui a déjà la session authentifiée définie
            if self.auth_service and self.auth_service.supabase:
                return self.auth_service.supabase
            
            # Fallback sur notre propre client (non authentifié)
            return self.supabase
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du client authentifié: {e}")
            return self.supabase
    
    async def _load_subscription_from_supabase(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Charge l'abonnement actif depuis Supabase
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Données de l'abonnement ou None
        """
        try:
            client = self._get_authenticated_client()
            if not client:
                return None
            
            response = client.table('subscriptions') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('status', 'active') \
                .order('expires_at', desc=True) \
                .limit(1) \
                .execute()
            
            if response.data and len(response.data) > 0:
                subscription = response.data[0]
                
                # Vérifier si l'abonnement est expiré
                expires_at_str = subscription['expires_at']
                if 'T' in expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                else:
                    expires_at = datetime.fromisoformat(expires_at_str)
                
                # Corriger le problème de timezone
                from datetime import timezone
                now = datetime.now(timezone.utc)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                if expires_at > now:
                    return subscription
                else:
                    # Marquer comme expiré
                    await self._update_subscription_status(subscription['id'], 'expired')
                    return None
            
            return None
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'abonnement depuis Supabase: {e}")
            return None
    
    async def _load_subscription_with_retry(self, user_id: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Charge l'abonnement avec retry (pour gérer les délais de propagation Supabase)
        
        Args:
            user_id: ID de l'utilisateur
            max_retries: Nombre maximum de tentatives
            
        Returns:
            Données de l'abonnement ou None
        """
        for attempt in range(max_retries):
            subscription = await self._load_subscription_from_supabase(user_id)
            if subscription:
                return subscription
            
            if attempt < max_retries - 1:
                delay = 0.5 * (2 ** attempt)  # Backoff exponentiel: 0.5s, 1s, 2s
                await asyncio.sleep(delay)
        
        return None
    
    async def _save_subscription_to_supabase(self, user_id: str, invoice_id: str, expires_at: datetime) -> bool:
        """
        Sauvegarde un nouvel abonnement dans Supabase
        
        Args:
            user_id: ID de l'utilisateur
            invoice_id: ID de la facture BTCPay
            expires_at: Date d'expiration de l'abonnement
            
        Returns:
            Succès de l'opération
        """
        try:
            client = self._get_authenticated_client()
            if not client:
                logger.error("Supabase non initialisé")
                return False
            
            from datetime import timezone
            
            data = {
                'user_id': user_id,
                'invoice_id': invoice_id,
                'status': 'active',
                'activated_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': expires_at.astimezone(timezone.utc).isoformat() if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc).isoformat(),
                'auto_renew': True
            }
            
            response = client.table('subscriptions').insert(data).execute()
            
            if response.data:
                return True
            else:
                logger.error("Échec de la sauvegarde de l'abonnement dans Supabase")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'abonnement dans Supabase: {e}")
            return False
    
    async def _update_subscription_status(self, subscription_id: str, status: str) -> bool:
        """
        Met à jour le statut d'un abonnement
        
        Args:
            subscription_id: ID de l'abonnement
            status: Nouveau statut
            
        Returns:
            Succès de l'opération
        """
        try:
            client = self._get_authenticated_client()
            if not client:
                return False
            
            response = client.table('subscriptions') \
                .update({'status': status, 'updated_at': datetime.now().isoformat()}) \
                .eq('id', subscription_id) \
                .execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut: {e}")
            return False
    
    async def create_invoice(self, user_id: str, user_email: str) -> tuple[bool, str, Optional[Dict]]:
        """
        Crée une facture BTCPay pour l'abonnement mensuel
        
        Args:
            user_id: ID de l'utilisateur
            user_email: Email de l'utilisateur
        
        Returns:
            (succès, message, données_facture)
        """
        try:
            server_url = self.btcpay_config.get('server_url', '')
            store_id = self.btcpay_config.get('store_id', '')
            api_key = self.btcpay_config.get('api_key', '')
            
            if not all([server_url, store_id, api_key]):
                return False, "Configuration BTCPay incomplète", None
            
            # Préparer les données de la facture
            price_eur = self.btcpay_config.get('subscription_price', 24.99)
            
            # Conversion EUR vers USD (approximative, vous pouvez utiliser une API de taux de change)
            price_usd = round(price_eur * 1.08, 2)  # Taux approximatif
            
            invoice_data = {
                "amount": str(price_usd),
                "currency": "USD",
                "metadata": {
                    "orderId": f"sub_{user_id}_{datetime.now().timestamp()}",
                    "userId": user_id,
                    "userEmail": user_email,
                    "itemDesc": "Abonnement mensuel AutoTele",
                    "subscriptionType": "monthly"
                },
                "checkout": {
                    "speedPolicy": "MediumSpeed",
                    "paymentMethods": ["BTC"],
                    "expirationMinutes": 30,
                    "monitoringMinutes": 30,
                    "paymentTolerance": 0,
                    "redirectURL": None,
                    "redirectAutomatically": False,
                    "requiresRefundEmail": False,
                    "checkoutType": "V2"
                }
            }
            
            # Créer la facture via l'API BTCPay
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"token {api_key}",
                    "Content-Type": "application/json"
                }
                
                url = f"{server_url}/api/v1/stores/{store_id}/invoices"
                
                response = await client.post(url, json=invoice_data, headers=headers)
                
                if response.status_code == 200:
                    invoice = response.json()
                    
                    return True, "Facture créée avec succès", {
                        "invoice_id": invoice.get('id'),
                        "checkout_link": invoice.get('checkoutLink'),
                        "amount": price_usd,
                        "amount_eur": price_eur,
                        "currency": "USD",
                        "status": invoice.get('status'),
                        "created_at": datetime.now().isoformat()
                    }
                else:
                    error = response.text
                    logger.error(f"Erreur BTCPay: {response.status_code} - {error}")
                    return False, f"Erreur lors de la création de la facture: {response.status_code}", None
                    
        except Exception as e:
            logger.error(f"Erreur lors de la création de la facture: {e}")
            return False, f"Erreur: {str(e)}", None
    
    async def check_invoice_status(self, invoice_id: str) -> tuple[bool, str, Optional[str]]:
        """
        Vérifie le statut d'une facture BTCPay
        
        Args:
            invoice_id: ID de la facture
        
        Returns:
            (succès, message, statut)
        """
        try:
            server_url = self.btcpay_config.get('server_url', '')
            store_id = self.btcpay_config.get('store_id', '')
            api_key = self.btcpay_config.get('api_key', '')
            
            if not all([server_url, store_id, api_key]):
                return False, "Configuration BTCPay incomplète", None
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"token {api_key}",
                    "Content-Type": "application/json"
                }
                
                url = f"{server_url}/api/v1/stores/{store_id}/invoices/{invoice_id}"
                
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    invoice = response.json()
                    status = invoice.get('status')
                    
                    return True, "Statut récupéré", status
                else:
                    logger.error(f"Erreur lors de la vérification: {response.status_code}")
                    return False, "Erreur lors de la vérification", None
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de facture: {e}")
            return False, f"Erreur: {str(e)}", None
    
    async def activate_subscription(self, user_id: str, invoice_id: str, duration_days: int = 30):
        """
        Active l'abonnement après paiement réussi dans Supabase
        
        Args:
            user_id: ID de l'utilisateur
            invoice_id: ID de la facture payée
            duration_days: Durée de l'abonnement en jours
        """
        try:
            now = datetime.now()
            expires_at = now + timedelta(days=duration_days)
            
            # Sauvegarder dans Supabase
            success = await self._save_subscription_to_supabase(user_id, invoice_id, expires_at)
            
            if success:
                # NE PAS mettre à jour current_subscription ici !
                # Le timer auto-refresh détectera le changement dans les 2-6 secondes
                logger.info("Abonnement activé dans Supabase")
            else:
                logger.error("Échec de l'activation de l'abonnement dans Supabase")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'activation de l'abonnement: {e}")
    
    async def is_subscription_active_for_user(self, user_id: str) -> bool:
        """
        Vérifie si l'utilisateur a un abonnement actif dans Supabase
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            True si l'abonnement est actif
        """
        try:
            subscription = await self._load_subscription_from_supabase(user_id)
            return subscription is not None
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'abonnement: {e}")
            return False
    
    def is_subscription_active(self) -> bool:
        """Vérifie si l'abonnement en cache est actif (pour compatibilité)"""
        if not self.current_subscription:
            return False
        
        try:
            expires_at_str = self.current_subscription.get('expires_at', '')
            # Gérer les deux formats (avec/sans timezone)
            if 'T' in expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            else:
                expires_at = datetime.fromisoformat(expires_at_str)
            
            status = self.current_subscription.get('status', '')
            
            # Corriger le problème de timezone
            now = datetime.now()
            if expires_at.tzinfo is not None:
                # Si expires_at a une timezone, rendre now timezone-aware
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            elif now.tzinfo is not None:
                # Si now a une timezone mais pas expires_at, rendre expires_at timezone-naive
                expires_at = expires_at.replace(tzinfo=None)
            
            is_active = status == 'active' and now < expires_at
            return is_active
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'abonnement: {e}")
            return False
    
    def get_subscription_info(self) -> Optional[Dict[str, Any]]:
        """Retourne les informations de l'abonnement actuel"""
        if not self.current_subscription:
            return None
        
        try:
            expires_at_str = self.current_subscription.get('expires_at', '')
            if 'T' in expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            else:
                expires_at = datetime.fromisoformat(expires_at_str)
            
            # Corriger le problème de timezone
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            days_remaining = (expires_at - now).days
            
            return {
                "status": self.current_subscription.get('status'),
                "expires_at": expires_at,
                "days_remaining": max(0, days_remaining),
                "is_active": self.is_subscription_active(),
                "auto_renew": self.current_subscription.get('auto_renew', False)
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos d'abonnement: {e}")
            return None
    
    async def cancel_subscription(self):
        """Annule le renouvellement automatique de l'abonnement"""
        if self.current_subscription:
            self.current_subscription['auto_renew'] = False
            self._save_subscription_status()
    
    async def check_and_notify_expiration(self) -> Optional[str]:
        """
        Vérifie l'expiration et retourne un message si nécessaire
        
        Returns:
            Message d'avertissement ou None
        """
        info = self.get_subscription_info()
        if not info:
            return "Aucun abonnement actif"
        
        if not info['is_active']:
            return "Votre abonnement a expiré. Veuillez renouveler pour continuer."
        
        days_remaining = info['days_remaining']
        if days_remaining <= 3:
            return f"Votre abonnement expire dans {days_remaining} jour(s)"
        
        return None
    
    def get_price_display(self) -> str:
        """Retourne le prix formaté pour l'affichage"""
        price_eur = self.btcpay_config.get('subscription_price', 24.99)
        price_usd = round(price_eur * 1.08, 2)
        return f"${price_usd} USD"
    
    def get_subscription_status_display(self) -> dict:
        """
        Retourne les informations de statut d'abonnement pour l'affichage
        
        Returns:
            Dict avec 'color', 'text', 'days_remaining'
        """
        # Si pas d'abonnement en cache, essayer de charger depuis Supabase
        if not self.current_subscription:
            # Créer une tâche pour charger depuis Supabase
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si la boucle tourne, créer une tâche
                    asyncio.create_task(self._load_and_cache_subscription())
                else:
                    # Sinon, exécuter directement
                    loop.run_until_complete(self._load_and_cache_subscription())
            except Exception as e:
                logger.error(f"Erreur lors du rechargement de l'abonnement: {e}")
            
            # Vérifier à nouveau après tentative de rechargement
            if not self.current_subscription:
                return {
                    'color': 'red',
                    'text': 'Aucun abonnement',
                    'days_remaining': 0
                }
        
        try:
            expires_at_str = self.current_subscription.get('expires_at', '')
            if 'T' in expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            else:
                expires_at = datetime.fromisoformat(expires_at_str)
            
            # Corriger le problème de timezone
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            days_remaining = (expires_at - now).days
            status = self.current_subscription.get('status', '')
            
            if status != 'active' or days_remaining <= 0:
                return {
                    'color': 'red',
                    'text': 'Abonnement expiré',
                    'days_remaining': 0
                }
            elif days_remaining <= 1:
                return {
                    'color': 'red',
                    'text': f'Expire dans {days_remaining} jour',
                    'days_remaining': days_remaining
                }
            elif days_remaining <= 3:
                return {
                    'color': 'orange',
                    'text': f'Expire dans {days_remaining} jours',
                    'days_remaining': days_remaining
                }
            else:
                return {
                    'color': 'green',
                    'text': f'Actif ({days_remaining} jours)',
                    'days_remaining': days_remaining
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut: {e}")
            return {
                'color': 'red',
                'text': 'Erreur de statut',
                'days_remaining': 0
            }
    
    async def _load_and_cache_subscription(self):
        """Charge et met en cache l'abonnement depuis Supabase"""
        try:
            from services.auth_service import get_auth_service
            auth_service = get_auth_service()
            user_id = auth_service.get_user_id()
            
            if user_id:
                subscription = await self._load_subscription_from_supabase(user_id)
                if subscription:
                    self.current_subscription = subscription
        except Exception as e:
            logger.error(f"Erreur lors du rechargement de l'abonnement: {e}")
    
    async def get_btc_rate(self) -> Optional[float]:
        """Récupère le taux BTC/USD actuel"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://api.coinbase.com/v2/exchange-rates?currency=BTC")
                if response.status_code == 200:
                    data = response.json()
                    usd_rate = float(data['data']['rates']['USD'])
                    return usd_rate
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du taux BTC: {e}")
        return None
    
    def clear_subscription(self):
        """Efface les données d'abonnement du cache (lors de la déconnexion)"""
        # Ne plus utiliser de cache local - tout est dans Supabase
        self.current_subscription = None


# Instance singleton
_subscription_service = None

def get_subscription_service() -> SubscriptionService:
    """Retourne l'instance singleton du service d'abonnement"""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service

