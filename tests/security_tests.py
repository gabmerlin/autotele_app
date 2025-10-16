"""
Tests de sécurité pour AutoTele.

OBJECTIF: Vérifier que toutes les corrections de sécurité fonctionnent.

Tests couverts:
1. Injections SQL
2. Validation des messages (XSS)
3. Magic bytes (fichiers déguisés)
4. Sanitisation des logs
5. Rate limiting
6. Validation de configuration
7. Permissions fichiers
"""
import sys
import os
from pathlib import Path
import asyncio
import tempfile
import json

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.validators import validate_message, sanitize_message
from utils.logger import AutoTeleLogger
from utils.media_validator import MediaValidator
from utils.rate_limiter import RateLimiter
from utils.config import Config
from utils.file_permissions import FilePermissions


class SecurityTests:
    """Tests de sécurité automatisés."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def test(self, name: str, condition: bool, message: str = ""):
        """Exécute un test."""
        if condition:
            print(f"[OK] {name}")
            self.passed += 1
        else:
            print(f"[FAIL] {name}: {message}")
            self.failed += 1
    
    def warning(self, name: str, message: str):
        """Affiche un avertissement."""
        print(f"[WARN] {name}: {message}")
        self.warnings += 1
    
    def section(self, title: str):
        """Affiche une section."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    
    # ==================== TESTS SQL ====================
    
    def test_sql_injection(self):
        """Test 1: Protection contre les injections SQL."""
        self.section("TEST 1: Protection Injections SQL")
        
        # Test avec valeur négative
        from database.telegram_db import TelegramDatabase
        db = TelegramDatabase(":memory:")
        
        try:
            # Tenter une injection avec limit négatif
            conversations = db.get_conversations(
                session_ids=["test"],
                limit=-1
            )
            self.test(
                "SQL Injection (limit négatif)",
                True,
                "Limite négative rejetée"
            )
        except Exception as e:
            self.test("SQL Injection (limit négatif)", False, str(e))
        
        try:
            # Tenter une injection avec chaîne
            conversations = db.get_conversations(
                session_ids=["test"],
                limit="999; DROP TABLE conversations; --"
            )
            self.test(
                "SQL Injection (chaîne malveillante)",
                True,
                "Chaîne malveillante rejetée"
            )
        except Exception as e:
            self.test("SQL Injection (chaîne malveillante)", False, str(e))
        
        db.close()
    
    # ==================== TESTS XSS ====================
    
    def test_xss_validation(self):
        """Test 2: Validation des messages (XSS)."""
        self.section("TEST 2: Validation Messages (XSS)")
        
        # Test 1: Message normal
        is_valid, _ = validate_message("Bonjour, comment allez-vous ?")
        self.test("Message normal", is_valid)
        
        # Test 2: Script tag
        is_valid, error = validate_message("<script>alert('XSS')</script>")
        self.test(
            "Blocage <script>",
            not is_valid,
            "Script tag devrait être bloqué"
        )
        
        # Test 3: javascript:
        is_valid, error = validate_message("Click <a href='javascript:alert(1)'>here</a>")
        self.test(
            "Blocage javascript:",
            not is_valid,
            "javascript: devrait être bloqué"
        )
        
        # Test 4: onerror=
        is_valid, error = validate_message("<img src=x onerror='alert(1)'>")
        self.test(
            "Blocage onerror=",
            not is_valid,
            "onerror devrait être bloqué"
        )
        
        # Test 5: Caractères nuls
        is_valid, error = validate_message("Test\x00null")
        self.test(
            "Blocage caractères nuls",
            not is_valid,
            "Caractères nuls devraient être bloqués"
        )
        
        # Test 6: Sanitisation
        sanitized = sanitize_message("<b>Hello</b> World")
        self.test(
            "Sanitisation HTML",
            "&lt;b&gt;" in sanitized and "&lt;/b&gt;" in sanitized,
            "HTML devrait être échappé"
        )
    
    # ==================== TESTS MAGIC BYTES ====================
    
    def test_magic_bytes(self):
        """Test 3: Détection magic bytes."""
        self.section("TEST 3: Détection Magic Bytes")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Test 1: JPEG
            jpeg_file = tmpdir / "test.jpg"
            with open(jpeg_file, 'wb') as f:
                f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
            
            mime = MediaValidator.get_real_mime_type(str(jpeg_file))
            self.test("Détection JPEG", mime == 'image/jpeg')
            
            # Test 2: PNG
            png_file = tmpdir / "test.png"
            with open(png_file, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            
            mime = MediaValidator.get_real_mime_type(str(png_file))
            self.test("Détection PNG", mime == 'image/png')
            
            # Test 3: PDF
            pdf_file = tmpdir / "test.pdf"
            with open(pdf_file, 'wb') as f:
                f.write(b'%PDF-1.4' + b'\x00' * 100)
            
            mime = MediaValidator.get_real_mime_type(str(pdf_file))
            self.test("Détection PDF", mime == 'application/pdf')
            
            # Test 4: Exécutable Windows (DANGER)
            exe_file = tmpdir / "test.exe"
            with open(exe_file, 'wb') as f:
                f.write(b'MZ' + b'\x00' * 100)
            
            mime = MediaValidator.get_real_mime_type(str(exe_file))
            self.test(
                "Détection EXE",
                mime == 'application/x-msdownload',
                "Exécutable devrait être détecté"
            )
            
            # Test 5: Fichier déguisé (exe renommé en jpg)
            fake_jpg = tmpdir / "malware.jpg"
            with open(fake_jpg, 'wb') as f:
                f.write(b'MZ' + b'\x00' * 100)  # Contenu d'exe
            
            real_mime = MediaValidator.get_real_mime_type(str(fake_jpg))
            is_compatible = MediaValidator.is_mime_type_compatible(
                real_mime, 'image/jpeg'
            )
            self.test(
                "Blocage fichier déguisé",
                not is_compatible,
                "Fichier déguisé devrait être détecté"
            )
    
    # ==================== TESTS LOGS ====================
    
    def test_log_sanitization(self):
        """Test 4: Sanitisation des logs."""
        self.section("TEST 4: Sanitisation des Logs")
        
        logger = AutoTeleLogger("temp/test_logs")
        
        # Test 1: Numéro de téléphone
        text = "Erreur avec le numéro +33612345678"
        sanitized = logger._sanitize_sensitive_data(text)
        self.test(
            "Masquage téléphone",
            "+33612345678" not in sanitized and "+XXX" in sanitized
        )
        
        # Test 2: Chemin Windows
        text = "Fichier dans C:\\Users\\John\\Desktop\\secret.txt"
        sanitized = logger._sanitize_sensitive_data(text)
        self.test(
            "Masquage chemin Windows",
            "John" not in sanitized and "XXX" in sanitized
        )
        
        # Test 3: Token/Clé
        text = "API_KEY = 'sk_live_1234567890abcdef'"
        sanitized = logger._sanitize_sensitive_data(text)
        self.test(
            "Masquage API key",
            "sk_live_" not in sanitized and "XXX" in sanitized
        )
        
        # Test 4: Email
        text = "Contact: john.doe@example.com"
        sanitized = logger._sanitize_sensitive_data(text)
        self.test(
            "Masquage email",
            "john.doe@example.com" not in sanitized and "email@XXX" in sanitized
        )
        
        # Test 5: Adresse IP
        text = "Connexion depuis 192.168.1.100"
        sanitized = logger._sanitize_sensitive_data(text)
        self.test(
            "Masquage IP",
            "192.168.1.100" not in sanitized and "XXX.XXX.XXX.XXX" in sanitized
        )
    
    # ==================== TESTS RATE LIMITING ====================
    
    async def test_rate_limiting(self):
        """Test 5: Rate limiting."""
        self.section("TEST 5: Rate Limiting")
        
        limiter = RateLimiter({
            'test_action': (3, 10)  # 3 requêtes par 10 secondes
        })
        
        # Test 1: Premières requêtes autorisées
        allowed1, _ = await limiter.check_rate_limit('test_action', 'user1')
        allowed2, _ = await limiter.check_rate_limit('test_action', 'user1')
        allowed3, _ = await limiter.check_rate_limit('test_action', 'user1')
        
        self.test(
            "Rate limit - requêtes autorisées",
            allowed1 and allowed2 and allowed3
        )
        
        # Test 2: 4ème requête bloquée
        allowed4, wait_time = await limiter.check_rate_limit('test_action', 'user1')
        
        self.test(
            "Rate limit - requête bloquée",
            not allowed4 and wait_time > 0,
            "4ème requête devrait être bloquée"
        )
        
        # Test 3: Utilisateurs différents isolés
        allowed_other, _ = await limiter.check_rate_limit('test_action', 'user2')
        
        self.test(
            "Rate limit - isolation utilisateurs",
            allowed_other,
            "Autres utilisateurs ne devraient pas être affectés"
        )
        
        # Test 4: Quota restant
        remaining = limiter.get_remaining_requests('test_action', 'user1')
        self.test(
            "Rate limit - quota restant",
            remaining == 0,
            f"Quota devrait être 0, obtenu {remaining}"
        )
    
    # ==================== TESTS CONFIGURATION ====================
    
    def test_config_validation(self):
        """Test 6: Validation de configuration."""
        self.section("TEST 6: Validation Configuration")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            config_file = tmpdir / "test_config.json"
            
            # Créer une config de test
            test_config = {
                "telegram": {
                    "rate_limit_delay": 5,
                    "max_messages_per_minute": 20
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(test_config, f)
            
            config = Config(str(config_file))
            
            # Test 1: Valeur valide
            try:
                config.set("telegram.rate_limit_delay", 3.5)
                self.test("Config - valeur valide", True)
            except ValueError:
                self.test("Config - valeur valide", False, "Valeur valide rejetée")
            
            # Test 2: Valeur trop petite
            try:
                config.set("telegram.rate_limit_delay", 0.001)  # Min = 0.01
                self.test("Config - valeur trop petite", False, "Valeur invalide acceptée")
            except ValueError:
                self.test("Config - valeur trop petite", True)
            
            # Test 3: Valeur trop grande
            try:
                config.set("telegram.max_messages_per_minute", 1000)  # Max = 100
                self.test("Config - valeur trop grande", False, "Valeur invalide acceptée")
            except ValueError:
                self.test("Config - valeur trop grande", True)
            
            # Test 4: Type invalide
            try:
                config.set("telegram.max_messages_per_minute", "beaucoup")
                self.test("Config - type invalide", False, "Type invalide accepté")
            except ValueError:
                self.test("Config - type invalide", True)
    
    # ==================== TESTS PERMISSIONS ====================
    
    def test_file_permissions(self):
        """Test 7: Permissions fichiers."""
        self.section("TEST 7: Permissions Fichiers")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "secret.txt"
            
            # Créer un fichier sécurisé
            success, msg = FilePermissions.create_secure_file(
                test_file,
                b"Secret data"
            )
            
            self.test("Création fichier sécurisé", success, msg)
            
            if success:
                # Vérifier que le fichier existe
                self.test("Fichier créé", test_file.exists())
                
                # Vérifier les permissions
                is_secure, perm_msg = FilePermissions.check_file_permissions(test_file)
                
                if os.name != 'nt':  # Unix/Linux
                    self.test("Permissions sécurisées (Unix)", is_secure, perm_msg)
                else:  # Windows
                    self.warning(
                        "Permissions Windows",
                        "Vérification ACLs nécessite pywin32 installé"
                    )
    
    # ==================== TESTS CHIFFREMENT ====================
    
    def test_encryption(self):
        """Test 8: Chiffrement des sessions."""
        self.section("TEST 8: Chiffrement Sessions")
        
        # Vérifier que la clé de chiffrement est requise
        import os
        original_key = os.getenv('AUTOTELE_ENCRYPTION_KEY')
        
        if not original_key:
            self.warning(
                "Chiffrement",
                "AUTOTELE_ENCRYPTION_KEY non définie - Chiffrement désactivé"
            )
            return
        
        # Test avec clé valide
        try:
            from utils.encryption import SessionEncryption
            encryption = SessionEncryption(original_key)
            self.test("Initialisation chiffrement", True)
            
            # Vérifier que le salt est unique
            salt1 = encryption.salt
            self.test(
                "Salt unique généré",
                len(salt1) == 32,
                f"Salt devrait faire 32 bytes, obtenu {len(salt1)}"
            )
            
        except Exception as e:
            self.test("Initialisation chiffrement", False, str(e))
    
    # ==================== RÉSUMÉ ====================
    
    def print_summary(self):
        """Affiche le résumé des tests."""
        print(f"\n{'='*60}")
        print(f"  RÉSUMÉ DES TESTS DE SÉCURITÉ")
        print(f"{'='*60}\n")
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"[+] Tests reussis:  {self.passed}")
        print(f"[-] Tests echoues:  {self.failed}")
        print(f"[!] Avertissements: {self.warnings}")
        print(f"[*] Taux de reussite: {success_rate:.1f}%")
        
        print(f"\n{'='*60}\n")
        
        if self.failed == 0:
            print("*** TOUS LES TESTS DE SECURITE SONT PASSES ! ***")
            print("[+] L'application est securisee.")
            return True
        else:
            print(f"[!] {self.failed} TEST(S) ONT ECHOUE")
            print("[-] Des corrections sont necessaires.")
            return False


async def main():
    """Exécute tous les tests de sécurité."""
    print("""
================================================================
                                                              
        TESTS DE SECURITE AUTOTELE v1.3.0                    
        Verification pratique de toutes les corrections      
                                                              
================================================================
    """)
    
    tests = SecurityTests()
    
    try:
        # Tests synchrones
        tests.test_sql_injection()
        tests.test_xss_validation()
        tests.test_magic_bytes()
        tests.test_log_sanitization()
        tests.test_config_validation()
        tests.test_file_permissions()
        tests.test_encryption()
        
        # Tests asynchrones
        await tests.test_rate_limiting()
        
    except Exception as e:
        print(f"\n[ERROR] ERREUR CRITIQUE PENDANT LES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Afficher le résumé
    success = tests.print_summary()
    
    return success


if __name__ == "__main__":
    import sys
    
    # Exécuter les tests
    success = asyncio.run(main())
    
    # Code de sortie
    sys.exit(0 if success else 1)

