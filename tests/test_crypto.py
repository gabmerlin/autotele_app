"""
Tests pour le module de chiffrement
"""
import pytest
import os
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.crypto import SessionEncryptor, hash_password, generate_token


class TestSessionEncryptor:
    """Tests pour SessionEncryptor"""
    
    def test_init_with_password(self):
        """Test d'initialisation avec mot de passe"""
        encryptor = SessionEncryptor("test_password")
        assert encryptor is not None
        assert encryptor.key is not None
        assert encryptor.cipher is not None
    
    def test_init_without_password(self):
        """Test d'initialisation sans mot de passe (utilise machine_id)"""
        encryptor = SessionEncryptor()
        assert encryptor is not None
    
    def test_encrypt_decrypt_session(self):
        """Test de chiffrement/déchiffrement de données"""
        encryptor = SessionEncryptor("test_password")
        
        original_data = b"Telegram session data 123456"
        
        # Chiffrer
        encrypted = encryptor.encrypt_session(original_data)
        assert encrypted != original_data
        assert len(encrypted) > len(original_data)  # Ajout de métadonnées
        
        # Déchiffrer
        decrypted = encryptor.decrypt_session(encrypted)
        assert decrypted == original_data
    
    def test_encrypt_decrypt_different_data(self):
        """Test avec différentes données"""
        encryptor = SessionEncryptor("test_password")
        
        test_cases = [
            b"",  # Vide
            b"a",  # Un caractère
            b"x" * 1000,  # Grande taille
            b"Unicode: \xc3\xa9\xc3\xa8\xc3\xa0",  # UTF-8
        ]
        
        for data in test_cases:
            encrypted = encryptor.encrypt_session(data)
            decrypted = encryptor.decrypt_session(encrypted)
            assert decrypted == data
    
    def test_different_passwords_different_results(self):
        """Test que différents mots de passe donnent différents résultats"""
        data = b"test data"
        
        enc1 = SessionEncryptor("password1")
        enc2 = SessionEncryptor("password2")
        
        encrypted1 = enc1.encrypt_session(data)
        encrypted2 = enc2.encrypt_session(data)
        
        assert encrypted1 != encrypted2
    
    def test_wrong_password_fails(self):
        """Test que le déchiffrement avec le mauvais mot de passe échoue"""
        data = b"secret data"
        
        enc1 = SessionEncryptor("correct_password")
        enc2 = SessionEncryptor("wrong_password")
        
        encrypted = enc1.encrypt_session(data)
        
        with pytest.raises(Exception):  # Fernet lève une exception
            enc2.decrypt_session(encrypted)
    
    def test_encrypt_decrypt_file(self):
        """Test de chiffrement/déchiffrement de fichier"""
        encryptor = SessionEncryptor("test_password")
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            input_file = f.name
            f.write(b"Test file content 123")
        
        try:
            encrypted_file = input_file + ".enc"
            output_file = input_file + ".dec"
            
            # Chiffrer
            encryptor.encrypt_file(input_file, encrypted_file)
            assert os.path.exists(encrypted_file)
            
            # Vérifier que le fichier chiffré est différent
            with open(input_file, 'rb') as f1, open(encrypted_file, 'rb') as f2:
                assert f1.read() != f2.read()
            
            # Déchiffrer
            encryptor.decrypt_file(encrypted_file, output_file)
            assert os.path.exists(output_file)
            
            # Vérifier que le contenu est identique
            with open(input_file, 'rb') as f1, open(output_file, 'rb') as f2:
                assert f1.read() == f2.read()
        
        finally:
            # Nettoyer
            for f in [input_file, encrypted_file, output_file]:
                if os.path.exists(f):
                    os.unlink(f)


class TestUtilityFunctions:
    """Tests pour les fonctions utilitaires"""
    
    def test_hash_password(self):
        """Test du hashing de mot de passe"""
        password = "my_secret_password"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert len(hashed) == 64  # SHA-256 = 64 caractères hex
        assert hashed != password
        
        # Le même mot de passe donne le même hash
        hashed2 = hash_password(password)
        assert hashed == hashed2
        
        # Un mot de passe différent donne un hash différent
        hashed3 = hash_password("different_password")
        assert hashed != hashed3
    
    def test_generate_token(self):
        """Test de génération de token"""
        token1 = generate_token()
        assert token1 is not None
        assert len(token1) == 32  # Longueur par défaut
        
        # Générer un token de longueur différente
        token2 = generate_token(16)
        assert len(token2) == 16
        
        # Les tokens sont uniques
        token3 = generate_token()
        assert token1 != token3
    
    def test_generate_token_length(self):
        """Test de différentes longueurs de token"""
        for length in [8, 16, 32, 64]:
            token = generate_token(length)
            assert len(token) == length

