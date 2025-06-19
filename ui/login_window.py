from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QCursor, QKeyEvent, QPixmap 
from PyQt5.QtCore import Qt
from firebase.auth_manager import AuthManager
from .styles import SIMPLE_STYLES
from pathlib import Path
import os

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.auth = AuthManager()
        self.on_login_success = on_login_success
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(SIMPLE_STYLES["main_window"])

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sol panel - Marka alanı
        brand_panel = self._create_brand_panel()

        # Sağ panel - Giriş formu
        login_panel = self._create_login_panel()

        main_layout.addWidget(brand_panel, 1)
        main_layout.addWidget(login_panel, 1)

    def _create_brand_panel(self):
        panel = QFrame()
        panel.setStyleSheet(SIMPLE_STYLES["brand_panel"])
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Logo Ekleme Başlangıcı ---
        logo_label = QLabel()
        
       # Get absolute path to assets folder
        BASE_DIR = Path(__file__).resolve().parent.parent
        logo_path = BASE_DIR / "assets" / "logo.png"

        # Debug print
        print(f"Base directory: {BASE_DIR}")
        print(f"Logo path: {logo_path}")
        print(f"Logo exists: {os.path.isfile(logo_path)}")
        
        if os.path.exists(logo_path):
            pixmap = QPixmap(str(logo_path))
            # Logoyu istediğiniz boyuta ölçeklendirin
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Örnek boyut
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        else:
            print(f"Uyarı: Logo dosyası bulunamadı: {logo_path}")
            # Opsiyonel: Logo bulunamazsa yerine bir yer tutucu metin veya ikon gösterilebilir
            placeholder_logo = QLabel("⚽") # Emoji olarak basit bir placeholder
            placeholder_logo.setStyleSheet("font-size: 100px; color: white;")
            placeholder_logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder_logo, alignment=Qt.AlignCenter)
        # --- Logo Ekleme Sonu ---

        app_name = QLabel("Football Match Anonymization")
        app_name.setStyleSheet(SIMPLE_STYLES["brand_title"])
        layout.addWidget(app_name, alignment=Qt.AlignCenter)

        tagline = QLabel("Transform football matches into 2D with AI.")
        tagline.setStyleSheet(SIMPLE_STYLES["brand_subtitle"])
        layout.addWidget(tagline, alignment=Qt.AlignCenter)

        return panel

    def _create_login_panel(self):
        panel = QFrame()
        panel.setStyleSheet(SIMPLE_STYLES["login_panel"])
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Login kartı
        login_card = QFrame()
        login_card.setStyleSheet(SIMPLE_STYLES["card"])
        login_card.setFixedWidth(350)
        card_layout = QVBoxLayout(login_card)
        card_layout.setSpacing(15)

        # Başlık
        title = QLabel("Login to Your Account")
        title.setStyleSheet(SIMPLE_STYLES["form_title"])
        card_layout.addWidget(title)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-Mail Adress")
        self.email_input.setStyleSheet(SIMPLE_STYLES["input_field"])
        

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(SIMPLE_STYLES["input_field"])

        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet(SIMPLE_STYLES["button_primary"])
        self.login_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.login_btn.clicked.connect(self.handle_login)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            QLabel {
                color: #ED4245;
                font-size: 12px;
                padding: 5px;
                margin-bottom: 5px;
                font-weight: bold;
            }
        """)
        self.error_label.hide()

        # Kart içeriğini birleştir - error_label'ı email_input'tan önce ekle
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.login_btn)
        card_layout.addSpacing(10)

        layout.addWidget(login_card)
        return panel

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.login_btn.click()
        else:
            super().keyPressEvent(event)

    def handle_login(self):
        result = self.auth.login_user(
            self.email_input.text(),
            self.password_input.text()
        )
        if result['success']:
            self.error_label.hide()
            self.email_input.setStyleSheet(SIMPLE_STYLES["input_field"])
            self.password_input.setStyleSheet(SIMPLE_STYLES["input_field"])
            self.on_login_success(result['uid'])
        else:
            self.error_label.setText("Mail veya password is incorrect.")
            self.error_label.show()
            self.email_input.clear()
            self.password_input.clear()