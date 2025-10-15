"""
Module de protection anti-debug et anti-analyse.
Détecte et empêche l'analyse de l'application.
"""
import ctypes
import sys
import os
import time
from typing import Callable
from utils.logger import get_logger

logger = get_logger()

class AntiDebug:
    """Classe de protection anti-debug"""
    
    def __init__(self):
        self.checks_enabled = True
        self.exit_on_detection = True
        self.corruption_mode = False
    
    def is_debugger_present(self) -> bool:
        """
        Détecte si un debugger est attaché au processus (Windows).
        Utilise l'API Windows IsDebuggerPresent.
        """
        try:
            return ctypes.windll.kernel32.IsDebuggerPresent() != 0
        except Exception:
            return False
    
    def check_remote_debugger(self) -> bool:
        """
        Détecte un debugger distant attaché au processus.
        Utilise l'API Windows CheckRemoteDebuggerPresent.
        """
        try:
            is_remote_present = ctypes.c_bool(False)
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(is_remote_present)
            )
            return is_remote_present.value
        except Exception:
            return False
    
    def check_parent_process(self) -> bool:
        """
        Vérifie si le processus parent est suspect.
        Détecte si l'application est lancée depuis un debugger.
        """
        try:
            import psutil
            current_process = psutil.Process(os.getpid())
            parent = current_process.parent()
            
            if parent is None:
                return False
            
            parent_name = parent.name().lower()
            
            # Liste de debuggers/analyseurs connus
            suspicious_parents = [
                'x64dbg', 'x32dbg', 'ollydbg', 'windbg',
                'ida', 'ida64', 'idaq', 'idaq64',
                'immunitydebugger', 'debugger',
                'processhacker', 'procexp', 'procexp64',
                'cheatengine', 'ce-x64', 'ce-x86'
            ]
            
            for suspicious in suspicious_parents:
                if suspicious in parent_name:
                    return True
            
            return False
            
        except ImportError:
            # psutil non disponible, ignorer cette vérification
            return False
        except Exception:
            return False
    
    def check_timing_attack(self) -> bool:
        """
        Détecte les attaques par timing (breakpoints, single-step).
        Un debugger ralentit considérablement l'exécution.
        """
        try:
            start = time.perf_counter()
            
            # Opération simple qui devrait être rapide
            dummy = sum(range(10000))
            
            end = time.perf_counter()
            elapsed = (end - start) * 1000  # ms
            
            # Si ça prend plus de 10ms, c'est suspect
            # (devrait prendre < 1ms normalement)
            return elapsed > 10.0
            
        except Exception:
            return False
    
    def check_vm_environment(self) -> bool:
        """
        Détecte si l'application tourne dans une VM ou sandbox.
        Les analystes utilisent souvent des VMs pour analyser les malwares.
        """
        try:
            # Vérifier les fichiers système typiques des VMs
            vm_files = [
                'C:\\windows\\system32\\drivers\\vmmouse.sys',
                'C:\\windows\\system32\\drivers\\vmhgfs.sys',
                'C:\\windows\\system32\\drivers\\VBoxMouse.sys',
                'C:\\windows\\system32\\drivers\\VBoxGuest.sys',
                'C:\\windows\\system32\\drivers\\VBoxSF.sys',
                'C:\\windows\\system32\\vboxdisp.dll',
                'C:\\windows\\system32\\vboxhook.dll',
                'C:\\windows\\system32\\vboxogl.dll',
            ]
            
            for vm_file in vm_files:
                if os.path.exists(vm_file):
                    return True
            
            # Vérifier les processus VM typiques
            try:
                import psutil
                for proc in psutil.process_iter(['name']):
                    proc_name = proc.info['name'].lower()
                    if any(vm in proc_name for vm in ['vmware', 'vbox', 'qemu', 'virtualbox']):
                        return True
            except ImportError:
                pass
            
            return False
            
        except Exception:
            return False
    
    def perform_checks(self) -> dict:
        """
        Exécute tous les tests anti-debug et retourne les résultats.
        
        Returns:
            dict: Résultats des tests avec les détections
        """
        if not self.checks_enabled:
            return {'all_clear': True}
        
        results = {
            'debugger_present': self.is_debugger_present(),
            'remote_debugger': self.check_remote_debugger(),
            'suspicious_parent': self.check_parent_process(),
            'timing_anomaly': self.check_timing_attack(),
            'vm_detected': self.check_vm_environment(),
        }
        
        results['detected'] = any(results.values())
        
        return results
    
    def handle_detection(self, detection_type: str):
        """
        Gère une détection de debug/analyse.
        
        Args:
            detection_type: Type de détection (debugger, vm, etc.)
        """
        logger.warning(f"Detection de securite: {detection_type}")
        
        if self.corruption_mode:
            # Mode corruption : corrompre les données pour rendre l'analyse inutile
            self._corrupt_memory()
        
        if self.exit_on_detection:
            # Quitter avec un message d'erreur générique
            print("Erreur critique: L'application a rencontre un probleme et doit fermer.")
            print("Code erreur: 0xC0000005 (ACCESS_VIOLATION)")
            time.sleep(1)
            sys.exit(1)
    
    def _corrupt_memory(self):
        """
        Corrompt volontairement les données chiffrées en mémoire.
        Rend l'analyse inutile car les secrets deviennent illisibles.
        """
        try:
            # Tenter de corrompre la config embarquée
            from utils import embedded_config
            if hasattr(embedded_config, '_ENCRYPTED_ENV'):
                # Remplacer par des données aléatoires
                embedded_config._ENCRYPTED_ENV = os.urandom(len(embedded_config._ENCRYPTED_ENV))
            if hasattr(embedded_config, '_ENCRYPTED_APP_CONFIG'):
                embedded_config._ENCRYPTED_APP_CONFIG = os.urandom(len(embedded_config._ENCRYPTED_APP_CONFIG))
        except Exception:
            pass
    
    def run_continuous_checks(self, interval: int = 30):
        """
        Lance des vérifications anti-debug en continu en arrière-plan.
        
        Args:
            interval: Intervalle entre les vérifications (secondes)
        """
        import threading
        
        def _check_loop():
            while self.checks_enabled:
                results = self.perform_checks()
                
                if results.get('detected'):
                    # Détection trouvée
                    for check_name, detected in results.items():
                        if detected and check_name != 'detected':
                            self.handle_detection(check_name)
                            return  # Sortir après détection
                
                time.sleep(interval)
        
        thread = threading.Thread(target=_check_loop, daemon=True)
        thread.start()
        logger.info("Verification anti-debug continue activee")


# Instance globale
_anti_debug = None

def get_anti_debug() -> AntiDebug:
    """Retourne l'instance globale d'anti-debug"""
    global _anti_debug
    if _anti_debug is None:
        _anti_debug = AntiDebug()
    return _anti_debug

def check_debug_on_startup(strict: bool = False):
    """
    Vérifie au démarrage si l'application est debugguée.
    
    Args:
        strict: Si True, active aussi la détection de VM
    """
    anti_debug = get_anti_debug()
    results = anti_debug.perform_checks()
    
    # En mode strict, inclure la détection de VM
    if strict:
        if results.get('detected'):
            logger.error("SECURITE: Environnement d'analyse detecte")
            anti_debug.handle_detection('startup_check')
    else:
        # Mode normal : ignorer la détection de VM (pour ne pas bloquer les utilisateurs en VM)
        if results.get('debugger_present') or results.get('remote_debugger'):
            logger.error("SECURITE: Debugger detecte")
            anti_debug.handle_detection('debugger')
    
    logger.info("Verification anti-debug au demarrage: OK")

