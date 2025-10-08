"""
Animations et effets visuels pour l'interface
"""
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSize
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect


class AnimationHelper:
    """Helper pour créer des animations fluides"""
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300):
        """Animation de fondu d'apparition"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animation.start()
        
        # Garder une référence pour éviter la destruction
        widget._fade_animation = animation
        return animation
    
    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300):
        """Animation de fondu de disparition"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animation.start()
        
        # Garder une référence pour éviter la destruction
        widget._fade_animation = animation
        return animation
    
    @staticmethod
    def slide_in(widget: QWidget, direction: str = "left", duration: int = 400):
        """
        Animation de glissement d'apparition
        
        Args:
            widget: Widget à animer
            direction: Direction ("left", "right", "top", "bottom")
            duration: Durée en millisecondes
        """
        start_pos = widget.pos()
        
        # Définir la position de départ selon la direction
        if direction == "left":
            offset = QPoint(-widget.width(), 0)
        elif direction == "right":
            offset = QPoint(widget.width(), 0)
        elif direction == "top":
            offset = QPoint(0, -widget.height())
        else:  # bottom
            offset = QPoint(0, widget.height())
        
        widget.move(start_pos + offset)
        
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos + offset)
        animation.setEndValue(start_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        
        # Garder une référence pour éviter la destruction
        widget._slide_animation = animation
        return animation
    
    @staticmethod
    def bounce_in(widget: QWidget, duration: int = 600):
        """Animation de rebond à l'apparition"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        # Animation d'opacité
        opacity_anim = QPropertyAnimation(effect, b"opacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        # Animation de taille
        original_size = widget.size()
        size_anim = QPropertyAnimation(widget, b"size")
        size_anim.setDuration(duration)
        size_anim.setStartValue(QSize(0, 0))
        size_anim.setEndValue(original_size)
        size_anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        opacity_anim.start()
        size_anim.start()
        
        # Garder les références
        widget._bounce_opacity_anim = opacity_anim
        widget._bounce_size_anim = size_anim
        
        return opacity_anim, size_anim
    
    @staticmethod
    def pulse(widget: QWidget, duration: int = 1000, scale: float = 1.05):
        """
        Animation de pulsation (pour attirer l'attention)
        
        Args:
            widget: Widget à animer
            duration: Durée d'un cycle complet
            scale: Facteur d'agrandissement (1.05 = 5%)
        """
        original_size = widget.size()
        scaled_size = QSize(
            int(original_size.width() * scale),
            int(original_size.height() * scale)
        )
        
        animation = QPropertyAnimation(widget, b"size")
        animation.setDuration(duration // 2)
        animation.setStartValue(original_size)
        animation.setEndValue(scaled_size)
        animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        animation.setLoopCount(-1)  # Boucle infinie
        animation.start()
        
        # Garder une référence
        widget._pulse_animation = animation
        return animation
    
    @staticmethod
    def shake(widget: QWidget, intensity: int = 10, duration: int = 500):
        """
        Animation de secousse (pour signaler une erreur)
        
        Args:
            widget: Widget à animer
            intensity: Intensité du mouvement en pixels
            duration: Durée totale
        """
        original_pos = widget.pos()
        
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        
        # Créer une séquence de positions pour le mouvement de secousse
        steps = 8
        for i in range(steps):
            progress = i / steps
            if i % 2 == 0:
                offset = QPoint(intensity, 0)
            else:
                offset = QPoint(-intensity, 0)
            
            animation.setKeyValueAt(progress, original_pos + offset)
        
        animation.setEndValue(original_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        animation.start()
        
        # Garder une référence
        widget._shake_animation = animation
        return animation
    
    @staticmethod
    def smooth_scroll(widget: QWidget, target_value: int, duration: int = 300):
        """
        Défilement fluide pour les zones scrollables
        
        Args:
            widget: Widget scrollable (QScrollArea, QListWidget, etc.)
            target_value: Valeur cible de défilement
            duration: Durée de l'animation
        """
        try:
            # Pour QScrollArea
            scrollbar = widget.verticalScrollBar()
            
            animation = QPropertyAnimation(scrollbar, b"value")
            animation.setDuration(duration)
            animation.setStartValue(scrollbar.value())
            animation.setEndValue(target_value)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
            
            # Garder une référence
            widget._scroll_animation = animation
            return animation
        except AttributeError:
            # Si le widget n'a pas de scrollbar
            return None
    
    @staticmethod
    def highlight_flash(widget: QWidget, color: str = "#4A90E2", duration: int = 1000):
        """
        Animation de flash pour mettre en évidence un élément
        
        Args:
            widget: Widget à mettre en évidence
            color: Couleur du flash (format hex)
            duration: Durée totale
        """
        original_style = widget.styleSheet()
        
        # Animation avec changement de style
        widget.setStyleSheet(f"{original_style} background-color: {color};")
        
        # Utiliser un QTimer pour restaurer le style original
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(duration, lambda: widget.setStyleSheet(original_style))
    
    @staticmethod
    def expand_collapse(widget: QWidget, expand: bool = True, duration: int = 300):
        """
        Animation d'expansion/réduction de hauteur
        
        Args:
            widget: Widget à animer
            expand: True pour étendre, False pour réduire
            duration: Durée de l'animation
        """
        animation = QPropertyAnimation(widget, b"maximumHeight")
        animation.setDuration(duration)
        
        if expand:
            animation.setStartValue(0)
            animation.setEndValue(widget.sizeHint().height())
        else:
            animation.setStartValue(widget.height())
            animation.setEndValue(0)
        
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animation.start()
        
        # Garder une référence
        widget._expand_animation = animation
        return animation


def apply_hover_effect(widget: QWidget):
    """
    Applique un effet de survol subtil à un widget
    
    Args:
        widget: Widget sur lequel appliquer l'effet
    """
    original_style = widget.styleSheet()
    
    def on_enter(event):
        widget.setStyleSheet(f"{original_style} background-color: rgba(74, 144, 226, 0.1);")
        event.accept()
    
    def on_leave(event):
        widget.setStyleSheet(original_style)
        event.accept()
    
    widget.enterEvent = on_enter
    widget.leaveEvent = on_leave


def apply_button_press_effect(button):
    """
    Applique un effet de pression visuel à un bouton
    
    Args:
        button: Bouton sur lequel appliquer l'effet
    """
    from PyQt6.QtCore import QTimer
    
    original_style = button.styleSheet()
    
    def on_press():
        button.setStyleSheet(f"{original_style} transform: scale(0.95);")
        QTimer.singleShot(100, lambda: button.setStyleSheet(original_style))
    
    button.pressed.connect(on_press)

