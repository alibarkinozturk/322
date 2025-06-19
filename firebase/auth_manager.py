from firebase.firebase_config import FirebaseConfig
import requests 

class AuthManager:
    def __init__(self):
        self.config = FirebaseConfig()
        self.API_KEY = "********"
    
    def login_user(self, email: str, password: str) -> dict:
        """
        Firebase REST API ile gerçek şifre doğrulama
        Doc: https://firebase.google.com/docs/reference/rest/auth
        """
        try:
            response = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.API_KEY}",
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }
            )
            
            if response.status_code == 200:
                return {'success': True, 'uid': response.json()['localId']}
            else:
                error_msg = response.json()['error']['message']
                return {'success': False, 'error': self._translate_error(error_msg)}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _translate_error(self, firebase_error: str) -> str:
        """Firebase hata mesajlarını kullanıcı dostu çeviriler"""
        error_mapping = {
            "EMAIL_NOT_FOUND": "Bu e-posta ile kayıtlı kullanıcı bulunamadı",
            "INVALID_PASSWORD": "Geçersiz şifre",
            "USER_DISABLED": "Hesap devre dışı bırakılmış",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Çok fazla deneme yapıldı, daha sonra tekrar deneyin"
        }
        return error_mapping.get(firebase_error, "Email veya şifre yanlış.")