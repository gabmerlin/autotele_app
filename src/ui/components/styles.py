"""
Styles CSS centralisés pour l'application.
"""
from typing import Final

# CSS Global de l'application
GLOBAL_CSS: Final[str] = '''
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    * {
        font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Supprimer tout scroll de la page */
    html, body {
        overflow: hidden !important;
        height: 100vh !important;
        width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Conteneur principal NiceGUI */
    .nicegui-content {
        overflow: hidden !important;
        height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .nicegui-content > div {
        margin: 0 !important;
        padding: 0 !important;
        height: 100vh !important;
        width: 100vw !important;
    }
    
    :root {
        --primary: #1e3a8a;
        --primary-light: #3b82f6;
        --secondary: #64748b;
        --accent: #0ea5e9;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --text-primary: #0f172a;
        --text-secondary: #64748b;
        --border: #e2e8f0;
    }
    
    .app-sidebar {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
        box-shadow: 4px 0 12px rgba(0, 0, 0, 0.08);
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    
    .sidebar-title {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .sidebar-btn {
        transition: all 0.2s ease;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .sidebar-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(4px);
    }
    
    .card-modern {
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid var(--border);
        transition: all 0.2s ease;
    }
    
    .card-modern:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .btn-primary {
        background: var(--primary);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    
    .btn-primary:hover {
        background: var(--primary-light);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
    }
    
    .status-badge {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .status-online {
        background: var(--success);
    }
    
    .status-offline {
        background: var(--danger);
    }
    
    /* Zone de contenu scrollable */
    .content-scrollable {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: 100%;
    }
    
    /* Masquer les icônes de notifications */
    .q-notification .q-icon,
    .q-notification__icon {
        display: none !important;
    }
    
    /* Scrollbar personnalisée */
    .custom-scrollbar::-webkit-scrollbar {
        width: 6px;
    }
    
    .custom-scrollbar::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 3px;
    }
    
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: var(--secondary);
        border-radius: 3px;
    }
    
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: var(--primary);
    }
    
    /* Zone d'upload de fichier */
    .file-upload-area:hover {
        background: rgba(30, 58, 138, 0.9) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(30, 58, 138, 0.3) !important;
    }
    
    .file-upload-area:active {
        transform: translateY(0) !important;
    }
    
    /* Barre de progression */
    .q-linear-progress {
        height: 28px !important;
        border-radius: 6px !important;
    }
    
    .q-linear-progress__track::after,
    .q-linear-progress__model::after,
    .q-linear-progress::after,
    .q-linear-progress::before,
    .q-linear-progress .q-linear-progress__text,
    .q-linear-progress span {
        content: '' !important;
        display: none !important;
        visibility: hidden !important;
    }
</style>
'''


def get_global_styles() -> str:
    """
    Retourne les styles CSS globaux de l'application.
    
    Returns:
        str: Code HTML contenant les styles CSS
    """
    return GLOBAL_CSS

