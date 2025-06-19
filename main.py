import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt
from ui.login_window import LoginWindow
from ui.dashboard_window import DashboardWindow
from pathlib import Path

def main():
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            
            # Pencere özelliklerini ayarla - özel başlık çubuğu için çerçevesiz
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            
            # Ana pencere stilini ayarla
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #121212;
                    border: 1px solid #333333;
                }
            """)
            
            # Özel başlık çubuğu ile ana widget oluştur
            self.setup_custom_window()
            
            # Login window oluşturulurken, başarılı giriş fonksiyonunu gönder
            self.login_window = LoginWindow(self.handle_login_success)
            # Dashboard oluşturulurken, logout fonksiyonunu da gönderelim
            self.dashboard = DashboardWindow(self.handle_logout)
            
            self.stacked_widget.addWidget(self.login_window)
            self.stacked_widget.addWidget(self.dashboard)
            
            # Uygulama başlığını ayarla
            self.setWindowTitle("Football Vision AI")
            
            # Pencere boyutunu ayarla
            self.setMinimumSize(1200, 800)
            
            # Uygulama logosunu ayarla (assets klasöründen)
            BASE_DIR = Path(__file__).parent
            logo_path = BASE_DIR / "assets" / "logo.png"
            
            if logo_path.exists():
                self.setWindowIcon(QIcon(str(logo_path)))
                print(f"Logo yüklendi: {logo_path}")
            else:
                print(f"Warning: Logo file not found at {logo_path}")
                # Alternatif logo yollarını dene
                alt_paths = [
                    BASE_DIR / "assets" / "logo.png",
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        self.setWindowIcon(QIcon(str(alt_path)))
                        print(f"Alternatif logo yüklendi: {alt_path}")
                        break
            
            # Pencereyi ekranın ortasına konumlandır
            self.center_window()
            
            # Sürükleme için değişkenler
            self.old_pos = None
            
            self.show_login()
        
        def setup_custom_window(self):
            """Özel başlık çubuğu ile ana pencere yapısını oluştur"""
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Özel başlık çubuğu
            title_bar = self.create_title_bar()
            main_layout.addWidget(title_bar)
            
            # Ana içerik alanı
            self.stacked_widget = QStackedWidget()
            self.stacked_widget.setStyleSheet("background-color: #2F3136;")
            main_layout.addWidget(self.stacked_widget)
        
        def create_title_bar(self):
            """Özel başlık çubuğu oluştur (Logolu)"""
            title_bar = QWidget()
            title_bar.setStyleSheet("""
                QWidget {
                    background-color: #1A1A1A;
                    border-bottom: 1px solid #333333;
                }
            """)
            title_bar.setFixedHeight(35)
            
            title_layout = QHBoxLayout(title_bar)
            title_layout.setContentsMargins(5, 0, 0, 0) # Sol boşluğu azalt
            title_layout.setSpacing(5) # İkon ve yazı arası boşluk
            
            # --- YENİ: Uygulama İkonu ---
            BASE_DIR = Path(__file__).parent
            logo_path = BASE_DIR / "assets" / "logo.png"
            if logo_path.exists():
                icon_label = QLabel()
                pixmap = QPixmap(str(logo_path))
                # İkonu başlık çubuğu yüksekliğine uygun ölçekle
                icon_label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                title_layout.addWidget(icon_label)
            # --- YENİ BÖLÜM SONU ---
            
            # Uygulama başlığı
            title_label = QLabel("322")
            title_label.setStyleSheet("""
                QLabel {
                    color: #FFFFFF; /* Rengi beyaz yaptık */
                    font-size: 16px; /* Boyutu ikona göre ayarladık */
                    font-weight: bold;
                    padding-top: 2px; /* Dikeyde ortalamak için */
                }
            """)
            title_layout.addWidget(title_label)
            
            title_layout.addStretch()
            
            # Pencere kontrol butonları (Bu kısım aynı kalıyor)
            button_style = """
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #BBBBBB;
                    font-size: 16px;
                    font-weight: bold;
                    min-width: 35px;
                    max-width: 35px;
                    min-height: 35px;
                    max-height: 35px;
                }
                QPushButton:hover {
                    background-color: #333333;
                    color: #FFFFFF;
                }
            """
            
            minimize_btn = QPushButton("−")
            minimize_btn.setStyleSheet(button_style)
            minimize_btn.clicked.connect(self.showMinimized)
            
            maximize_btn = QPushButton("□")
            maximize_btn.setStyleSheet(button_style)
            maximize_btn.clicked.connect(self.toggle_maximize)
            
            close_btn = QPushButton("×")
            close_btn.setStyleSheet(button_style + """
                QPushButton:hover {
                    background-color: #FF4444;
                    color: #FFFFFF;
                }
            """)
            close_btn.clicked.connect(self.close)
            
            title_layout.addWidget(minimize_btn)
            title_layout.addWidget(maximize_btn)
            title_layout.addWidget(close_btn)
            
            return title_bar
        
        def toggle_maximize(self):
            """Pencereyi maximize/restore et"""
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        
        def mousePressEvent(self, event):
            """Fare basma olayı - pencere sürükleme için"""
            if event.button() == Qt.LeftButton and event.y() <= 35:  # Sadece başlık çubuğunda
                self.old_pos = event.globalPos()
        
        def mouseMoveEvent(self, event):
            """Fare hareket olayı - pencere sürükleme"""
            if event.buttons() == Qt.LeftButton and self.old_pos and event.y() <= 35:
                delta = event.globalPos() - self.old_pos
                self.move(self.pos() + delta)
                self.old_pos = event.globalPos()
        
        def mouseReleaseEvent(self, event):
            """Fare bırakma olayı"""
            self.old_pos = None
        
        def center_window(self):
            """Pencereyi ekranın ortasına konumlandır"""
            from PyQt5.QtWidgets import QDesktopWidget
            desktop = QDesktopWidget()
            screen_geometry = desktop.screenGeometry()
            
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
        
        def show_login(self):
            self.stacked_widget.setCurrentIndex(0)
        
        def handle_login_success(self, uid):
            self.dashboard.set_user(uid)
            self.stacked_widget.setCurrentIndex(1)
            
        def handle_logout(self):
            # Çıkış yapıldığında giriş ekranına geri dön
            self.show_login()
            
            # Login ekranındaki alanları temizle
            self.login_window.email_input.clear()
            self.login_window.password_input.clear()

    app = QApplication(sys.argv)
    
    # Uygulama stilini ayarla
    app.setStyle('Fusion')  # Modern görünüm için
    
    # Genel font ayarları
    app_font = QFont("Segoe UI", 10)
    app.setFont(app_font)
    
    # Uygulama geneli koyu tema
    app.setStyleSheet("""
        QApplication {
            background-color: #121212;
        }
        QToolTip {
            background-color: #2A2A2A;
            color: white;
            border: 1px solid #4CAF50;
            padding: 5px;
            border-radius: 3px;
        }
    """)
    
    window = MainWindow()
    window.show()
    
    # Uygulama kapatılırken temizlik
    def cleanup():
        print("Uygulama kapatılıyor, temizlik yapılıyor...")
        # Geçici dosyaları temizle
        import shutil
        temp_dirs = ["temp_frames"]
        for temp_dir in temp_dirs:
            if Path(temp_dir).exists():
                try:
                    shutil.rmtree(temp_dir)
                    print(f"Temizlendi: {temp_dir}")
                except Exception as e:
                    print(f"Temizlik hatası {temp_dir}: {e}")
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()