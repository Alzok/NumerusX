from cryptography.fernet import Fernet

class SecurityManager:
    def __init__(self):
        self.cipher = Fernet(os.getenv("ENCRYPTION_KEY"))
    
    def encrypt_data(self, data):
        return self.cipher.encrypt(data.encode())
    
    def decrypt_data(self, encrypted):
        return self.cipher.decrypt(encrypted).decode()