import firebase_admin
from firebase_admin import credentials, firestore, auth

class FirebaseConfig:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            # Dosya yolunu düzeltin (proje köküne göre)
            cred = credentials.Certificate("serviceAccountKey.json")  # "/" işaretini kaldırın
            firebase_admin.initialize_app(cred)
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def db(self):
        return firestore.client()
    
    @property
    def auth_client(self):  # Metot ismini düzeltin (auth.client -> auth_client)
        return auth