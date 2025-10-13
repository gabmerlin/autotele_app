"""
Composant de dialogue de paiement BTCPay
"""
from nicegui import ui
from typing import Callable, Optional
import asyncio

from services.subscription_service import get_subscription_service
from services.auth_service import get_auth_service
from utils.logger import get_logger
from ui.components.svg_icons import svg

logger = get_logger()


class PaymentDialog:
    """Dialogue de paiement BTCPay pour l'abonnement"""
    
    def __init__(self, on_success: Optional[Callable] = None):
        """
        Args:
            on_success: Callback appelé après paiement réussi
        """
        self.subscription_service = get_subscription_service()
        self.auth_service = get_auth_service()
        self.on_success = on_success
        self.dialog = None
        self.invoice_data = None
        self.checking = False
        self.check_task = None
    
    async def show(self):
        """Affiche le dialogue de paiement"""
        # Créer la facture
        user_id = self.auth_service.get_user_id()
        user_email = self.auth_service.get_user_email()
        
        if not user_id or not user_email:
            ui.notify("Erreur: utilisateur non connecté", type='negative')
            return
        
        # Créer une notification de chargement
        notification = ui.notification("Création de la facture...", type='ongoing')
        
        success, message, invoice_data = await self.subscription_service.create_invoice(user_id, user_email)
        
        notification.dismiss()
        
        if not success or not invoice_data:
            ui.notify(f"Erreur: {message}", type='negative', timeout=5000)
            return
        
        self.invoice_data = invoice_data
        
        with ui.dialog().props('persistent') as self.dialog:
            with ui.card().classes('w-full p-0') \
                .style('max-width: 1200px; max-height: 85vh; overflow-y: auto; background: #ffffff; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); border: none;'):
                self._render_content()
        
        self.dialog.open()
        
        # Démarrer la vérification automatique du statut
        self.check_task = asyncio.create_task(self._auto_check_status())
    
    def _render_content(self):
        """Affiche le contenu du dialogue - Design professionnel cohérent avec l'app"""
        
        # EN-TÊTE BLEU (style sidebar de l'app)
        with ui.row().classes('w-full items-center justify-between p-6') \
            .style('background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); border-radius: 16px 16px 0 0;'):
            with ui.row().classes('items-center gap-3'):
                ui.html(svg('bolt', 32, 'white'))
                ui.label('AutoTele Premium').classes('text-2xl font-bold').style('color: white; font-family: Poppins; letter-spacing: -0.5px;')
            
            with ui.row().classes('items-center gap-2 px-3 py-1') \
                .style('background: rgba(255, 255, 255, 0.15); border-radius: 20px;'):
                ui.html(svg('verified', 16, 'white'))
                ui.label('Sécurisé').classes('text-xs font-medium text-white')
        
        # CONTENU PRINCIPAL
        with ui.column().classes('w-full px-8 py-6 gap-4'):
            
            # SECTION PRIX & INFO
            with ui.row().classes('w-full gap-6'):
                # Colonne gauche - Prix et features
                with ui.column().classes('gap-4').style('flex: 1;'):
                    # Prix
                    price_display = self.subscription_service.get_price_display()
                    with ui.card().classes('w-full p-6') \
                        .style('background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 12px;'):
                        ui.label('Abonnement mensuel').classes('text-sm font-medium').style('color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;')
                        ui.label(price_display).classes('text-4xl font-bold mt-2').style('color: #1e3a8a;')
                        ui.label('Renouvelé automatiquement chaque mois').classes('text-xs mt-2').style('color: #64748b;')
                    
                    # Features
                    with ui.column().classes('gap-3 mt-2'):
                        features = [
                            ('Accès illimité à toutes les fonctionnalités'),
                            ('Support prioritaire 7j/7'),
                            ('Mises à jour automatiques'),
                            ('Chiffrement de bout en bout')
                        ]
                        
                        for text in features:
                            with ui.row().classes('items-center gap-2'):
                                ui.html(svg('check_circle', 20, '#10b981'))
                                ui.label(text).classes('text-sm').style('color: #0f172a; font-weight: 500;')
                    
                    # Info sécurité
                    with ui.row().classes('items-center gap-2 mt-4 p-3') \
                        .style('background: #f0fdf4; border-left: 3px solid #10b981; border-radius: 8px;'):
                        ui.html(svg('lock', 18, '#064e3b'))
                        ui.label('Paiement 100% sécurisé').classes('text-sm font-semibold').style('color: #064e3b;')
                
                # Colonne droite - Interface de paiement
                with ui.column().classes('gap-3').style('flex: 1.5;'):
                    ui.label('Interface de paiement Bitcoin').classes('text-lg font-semibold').style('color: #0f172a;')
                    
                    checkout_link = self.invoice_data.get('checkout_link', '')
                    
                    if checkout_link:
                        # Container iframe avec style app
                        with ui.card().classes('w-full overflow-hidden') \
                            .style('border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);'):
                            
                            # Barre supérieure
                            with ui.row().classes('w-full items-center gap-2 px-4 py-3') \
                                .style('background: #1e3a8a; border-bottom: 1px solid rgba(255, 255, 255, 0.1);'):
                                ui.html(svg('lock', 16, 'white'))
                                ui.label('BTCPay Server - Paiement sécurisé').classes('text-sm font-medium text-white')
                            
                            # Iframe
                            ui.html(f'''
                                <iframe 
                                    src="{checkout_link}" 
                                    style="width: 100%; height: 500px; border: none; display: block; background: white;"
                                    allow="payment; camera; microphone"
                                    loading="lazy"
                                    sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
                                ></iframe>
                            ''')
                    else:
                        # Erreur
                        with ui.column().classes('w-full items-center justify-center p-12 gap-3') \
                            .style('background: #fef2f2; border: 2px solid #fecaca; border-radius: 12px;'):
                            ui.html(svg('error', 64, '#ef4444'))
                            ui.label('Erreur de chargement').classes('text-lg font-semibold').style('color: #ef4444;')
                            ui.label('Impossible de charger le module de paiement').classes('text-sm').style('color: #991b1b;')
            
            # SECTION STATUS
            with ui.row().classes('w-full items-center justify-between p-4 mt-4') \
                .style('background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px;'):
                with ui.row().classes('items-center gap-3'):
                    self.status_spinner = ui.spinner('dots', size='md').style('color: #3b82f6;')
                    self.status_label = ui.label('En attente de votre paiement...').classes('text-sm font-medium').style('color: #1e40af;')
                
                ui.button(icon='refresh', on_click=self._manual_check) \
                    .props('flat round dense') \
                    .style('color: #3b82f6;') \
                    .tooltip('Vérifier manuellement')
            
            # BOUTON ANNULER
            with ui.row().classes('w-full justify-center mt-2'):
                ui.button('Annuler', icon='close', on_click=self._handle_cancel) \
                    .props('outline') \
                    .classes('px-8') \
                    .style('color: #64748b; border-color: #cbd5e1; border-radius: 8px; font-weight: 500;')
            
    
    async def _auto_check_status(self):
        """Vérifie automatiquement le statut de la facture"""
        self.checking = True
        
        try:
            invoice_id = self.invoice_data.get('invoice_id')
            
            # Vérifier toutes les 5 secondes pendant 30 minutes max
            for _ in range(360):  # 360 * 5s = 30 minutes
                if not self.checking:
                    break
                
                await asyncio.sleep(5)
                
                success, _, status = await self.subscription_service.check_invoice_status(invoice_id)
                
                if success and status:
                    if status in ['Settled', 'Processing', 'Confirmed']:
                        # Paiement réussi !
                        await self._handle_payment_success()
                        break
                    elif status in ['Expired', 'Invalid']:
                        # Paiement échoué
                        self.status_label.text = 'Paiement expiré ou invalide'
                        self.status_label.classes('text-red-600 font-semibold')
                        self.status_spinner.visible = False
                        break
        
        except Exception as e:
            logger.error(f"Erreur lors de la vérification auto: {e}")
    
    async def _manual_check(self):
        """Vérification manuelle du statut"""
        invoice_id = self.invoice_data.get('invoice_id')
        
        notification = ui.notification("Vérification en cours...", type='ongoing')
        
        success, _, status = await self.subscription_service.check_invoice_status(invoice_id)
        
        notification.dismiss()
        
        if success and status:
            if status in ['Settled', 'Processing', 'Confirmed']:
                await self._handle_payment_success()
            elif status in ['Expired', 'Invalid']:
                ui.notify('Paiement expiré ou invalide', type='negative')
            else:
                ui.notify(f'Statut: {status}', type='info')
        else:
            ui.notify('Erreur lors de la vérification', type='negative')
    
    async def _handle_payment_success(self):
        """Gère le succès du paiement"""
        self.checking = False
        
        # Activer l'abonnement
        user_id = self.auth_service.get_user_id()
        invoice_id = self.invoice_data.get('invoice_id')
        
        await self.subscription_service.activate_subscription(user_id, invoice_id)
        
        # Fermer le dialogue immédiatement
        self.dialog.close()
        
        # Appeler le callback de succès avec un timer pour éviter les erreurs de contexte
        if self.on_success:
            ui.timer(0.1, lambda: asyncio.create_task(self.on_success()), once=True)
    
    def _handle_cancel(self):
        """Gère l'annulation"""
        self.checking = False
        if self.check_task:
            self.check_task.cancel()
        self.dialog.close()


class SubscriptionStatusCard:
    """Carte d'affichage du statut de l'abonnement"""
    
    def __init__(self):
        self.subscription_service = get_subscription_service()
        self.card = None
    
    def render(self):
        """Affiche la carte de statut d'abonnement"""
        info = self.subscription_service.get_subscription_info()
        
        if not info or not info['is_active']:
            # Abonnement inactif ou expiré
            with ui.card().classes('w-full bg-red-50 p-4') as self.card:
                with ui.row().classes('w-full items-center gap-3'):
                    ui.icon('warning', size='lg', color='red')
                    with ui.column().classes('flex-1'):
                        ui.label('Abonnement inactif').classes('font-semibold text-red-700')
                        ui.label('Veuillez renouveler votre abonnement pour continuer').classes('text-sm text-red-600')
                    ui.button('Souscrire', on_click=self._show_payment) \
                        .props('color=red')
        else:
            # Abonnement actif
            days_remaining = info['days_remaining']
            expires_at = info['expires_at'].strftime('%d/%m/%Y')
            
            # Couleur selon les jours restants
            if days_remaining <= 3:
                bg_color = 'bg-orange-50'
                text_color = 'text-orange-700'
                icon_color = 'orange'
            else:
                bg_color = 'bg-green-50'
                text_color = 'text-green-700'
                icon_color = 'green'
            
            with ui.card().classes(f'w-full {bg_color} p-4') as self.card:
                with ui.row().classes('w-full items-center gap-3'):
                    ui.icon('check_circle', size='lg', color=icon_color)
                    with ui.column().classes('flex-1'):
                        ui.label('Abonnement actif').classes(f'font-semibold {text_color}')
                        ui.label(f'Expire le {expires_at} ({days_remaining} jour(s) restant(s))') \
                            .classes(f'text-sm {text_color}')
                    
                    if days_remaining <= 7:
                        ui.button('Renouveler', on_click=self._show_payment) \
                            .props(f'color={icon_color} outline')
    
    async def _show_payment(self):
        """Affiche le dialogue de paiement"""
        dialog = PaymentDialog(on_success=self._refresh)
        await dialog.show()
    
    def _refresh(self):
        """Rafraîchit l'affichage"""
        if self.card:
            self.card.clear()
            with self.card:
                self.render()


async def show_payment_dialog(on_success: Optional[Callable] = None):
    """
    Affiche le dialogue de paiement BTCPay
    
    Args:
        on_success: Callback appelé après paiement réussi
    """
    dialog = PaymentDialog(on_success)
    await dialog.show()

