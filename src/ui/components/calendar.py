"""
Composant calendrier réutilisable pour la sélection de dates.
"""
from datetime import datetime, timedelta, date
from typing import Callable, Optional, Set
from nicegui import ui
from utils.constants import WEEKDAYS_SHORT, WEEKDAYS_LONG, MONTHS_LONG


class CalendarWidget:
    """Widget calendrier pour sélectionner des dates."""
    
    def __init__(
        self,
        on_date_change: Optional[Callable[[Set[date]], None]] = None,
        selected_dates: Optional[Set[date]] = None,
        compact: bool = False
    ):
        """
        Initialise le widget calendrier.
        
        Args:
            on_date_change: Fonction callback appelée quand les dates changent
            selected_dates: Dates déjà sélectionnées
            compact: Si True, affiche un calendrier compact
        """
        self.on_date_change = on_date_change
        self.selected_dates: Set[date] = selected_dates or set()
        self.compact = compact
        self.current_month = datetime.now().date().replace(day=1)
        self.container = None
    
    def render(self) -> ui.column:
        """
        Rend le calendrier dans un conteneur NiceGUI.
        
        Returns:
            ui.column: Le conteneur du calendrier
        """
        self.container = ui.column().classes('w-full h-full').style('overflow: hidden;')
        self._render_calendar()
        return self.container
    
    def _render_calendar(self) -> None:
        """Rend le calendrier."""
        if not self.container:
            return
        
        self.container.clear()
        
        with self.container:
            # En-tête avec navigation
            with ui.row().classes('w-full justify-between items-center mb-3 flex-shrink-0'):
                ui.button('◀', on_click=self._prev_month).props('flat dense')
                
                month_name = MONTHS_LONG[self.current_month.month - 1]
                year = self.current_month.year
                label_class = 'text-sm font-bold' if self.compact else 'text-lg font-bold'
                ui.label(f'{month_name} {year}').classes(label_class)
                
                ui.button('▶', on_click=self._next_month).props('flat dense')
            
            # Jours de la semaine
            weekdays = WEEKDAYS_SHORT if self.compact else WEEKDAYS_LONG
            gap_class = 'gap-1 mb-1' if self.compact else 'gap-1 mb-2'
            
            with ui.row().classes(f'w-full {gap_class} flex-shrink-0'):
                for day in weekdays:
                    font_class = 'text-xs' if self.compact else 'text-sm'
                    ui.label(day).classes(f'flex-1 text-center font-bold text-gray-600 {font_class}')
            
            # Grille du calendrier
            scroll_style = 'overflow-y: auto; padding-right: 8px;' if not self.compact else 'overflow: hidden;'
            
            with ui.column().classes('w-full flex-1').style(scroll_style):
                self._render_days()
    
    def _render_days(self) -> None:
        """Rend les jours du mois."""
        # Calculer le premier jour et le nombre de jours
        first_day = self.current_month.weekday()
        
        # Calculer le dernier jour du mois
        if self.current_month.month == 12:
            next_month = self.current_month.replace(year=self.current_month.year + 1, month=1, day=1)
        else:
            next_month = self.current_month.replace(month=self.current_month.month + 1, day=1)
        
        last_day = (next_month - timedelta(days=1)).day
        
        # Créer les lignes de semaines
        current_day = 1
        while current_day <= last_day:
            gap_class = 'gap-1 mb-1' if self.compact else 'gap-1 mb-1'
            with ui.row().classes(f'w-full {gap_class}'):
                for i in range(7):
                    if current_day == 1 and i < first_day:
                        # Jour vide au début
                        height = 'h-6' if self.compact else 'h-12'
                        ui.label('').classes(f'flex-1 {height}')
                    elif current_day <= last_day:
                        # Jour du mois
                        day_date = self.current_month.replace(day=current_day)
                        self._render_day_button(day_date)
                        current_day += 1
                    else:
                        # Jour vide à la fin
                        height = 'h-6' if self.compact else 'h-12'
                        ui.label('').classes(f'flex-1 {height}')
    
    def _render_day_button(self, day_date: date) -> None:
        """
        Rend un bouton de jour.
        
        Args:
            day_date: La date du jour à rendre
        """
        today = datetime.now().date()
        
        # Déterminer si le jour est cliquable et son style
        is_past = day_date <= today
        is_selected = day_date in self.selected_dates
        
        def toggle_date() -> None:
            """Toggle la sélection de la date."""
            if is_past:
                return
            
            if day_date in self.selected_dates:
                self.selected_dates.remove(day_date)
            else:
                self.selected_dates.add(day_date)
            
            if self.on_date_change:
                self.on_date_change(self.selected_dates)
            
            # Re-render
            self._render_calendar()
        
        # Créer le bouton
        btn = ui.button(str(day_date.day), on_click=toggle_date)
        height = 'h-6' if self.compact else 'h-12'
        btn.classes(f'flex-1 {height}')
        
        if self.compact:
            btn.props('dense')
        
        # Appliquer les couleurs
        if is_past:
            btn.props('color=grey disable')
        elif is_selected:
            btn.props('color=blue')
        else:
            btn.props('outline')
    
    def _prev_month(self) -> None:
        """Passe au mois précédent."""
        if self.current_month.month == 1:
            self.current_month = self.current_month.replace(
                year=self.current_month.year - 1,
                month=12
            )
        else:
            self.current_month = self.current_month.replace(
                month=self.current_month.month - 1
            )
        self._render_calendar()
    
    def _next_month(self) -> None:
        """Passe au mois suivant."""
        if self.current_month.month == 12:
            self.current_month = self.current_month.replace(
                year=self.current_month.year + 1,
                month=1
            )
        else:
            self.current_month = self.current_month.replace(
                month=self.current_month.month + 1
            )
        self._render_calendar()
    
    def clear_dates(self) -> None:
        """Efface toutes les dates sélectionnées."""
        self.selected_dates.clear()
        if self.on_date_change:
            self.on_date_change(self.selected_dates)
        self._render_calendar()
    
    def add_week(self) -> None:
        """Ajoute une semaine de dates."""
        today = datetime.now().date()
        for i in range(1, 8):
            future_date = today + timedelta(days=i)
            self.selected_dates.add(future_date)
        
        if self.on_date_change:
            self.on_date_change(self.selected_dates)
        self._render_calendar()
    
    def add_month(self) -> None:
        """Ajoute un mois de dates."""
        today = datetime.now().date()
        for i in range(1, 31):
            future_date = today + timedelta(days=i)
            self.selected_dates.add(future_date)
        
        if self.on_date_change:
            self.on_date_change(self.selected_dates)
        self._render_calendar()

