"""
Service de gestion des dialogues (groupes, canaux).
"""
from typing import List, Dict
from core.telegram.account import TelegramAccount
from utils.logger import get_logger

logger = get_logger()


class DialogService:
    """Service pour gérer les dialogues Telegram."""
    
    @staticmethod
    async def get_dialogs(account: TelegramAccount) -> List[Dict]:
        """
        Récupère tous les dialogues d'un compte.
        
        Args:
            account: Compte Telegram
            
        Returns:
            List[Dict]: Liste des dialogues
        """
        if not account or not account.is_connected:
            logger.warning("Tentative de récupération de dialogues avec compte non connecté")
            return []
        
        try:
            dialogs = await account.get_dialogs()            
            return dialogs
        except Exception as e:
            logger.error(f"Erreur récupération dialogues: {e}")
            return []
    
    @staticmethod
    def filter_dialogs(dialogs: List[Dict], search_text: str) -> List[Dict]:
        """
        Filtre les dialogues par texte de recherche.
        
        Args:
            dialogs: Liste des dialogues
            search_text: Texte à rechercher
            
        Returns:
            List[Dict]: Liste filtrée des dialogues
        """
        if not search_text:
            return dialogs
        
        search_lower = search_text.lower().strip()
        return [
            dialog for dialog in dialogs
            if search_lower in dialog['title'].lower()
        ]
    
    @staticmethod
    def count_selected(dialogs: List[Dict], selected_ids: List[int]) -> int:
        """
        Compte le nombre de dialogues sélectionnés parmi les dialogues filtrés.
        
        Args:
            dialogs: Liste des dialogues (filtré)
            selected_ids: Liste des IDs sélectionnés
            
        Returns:
            int: Nombre de dialogues sélectionnés
        """
        return len([d for d in dialogs if d['id'] in selected_ids])
    
    @staticmethod
    def get_dialog_info(dialogs: List[Dict], dialog_id: int) -> Dict:
        """
        Récupère les informations d'un dialogue spécifique.
        
        Args:
            dialogs: Liste des dialogues
            dialog_id: ID du dialogue
            
        Returns:
            Dict: Informations du dialogue ou dict vide
        """
        for dialog in dialogs:
            if dialog['id'] == dialog_id:
                return dialog
        return {}

