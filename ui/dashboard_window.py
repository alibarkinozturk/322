import os
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QLabel, QStackedWidget, QScrollArea, QMessageBox
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtCore import Qt, QObject, pyqtSignal

# Sayfa importları
from ui.pages.home_page import HomePageWidget
from ui.pages.my_videos_page import MyVideosPage
from ui.pages.analysis_results_page import AnalysisResultsPage


# Backend ve stil importları
from utils.backend import FrameProcessor, FrameAnnotator, VideoProcessor
from utils.config import SoccerPitchConfiguration
from ui.styles import SIMPLE_STYLES


class DashboardWindow(QWidget):
    def __init__(self, logout_callback=None):
        super().__init__()
        self.logout_callback = logout_callback
        self.user_id = None
        
        self._initialize_backend()
        self.init_ui()

    def _initialize_backend(self):
        try:
            self.soccer_config = SoccerPitchConfiguration()
            self.frame_processor = FrameProcessor(pitch_config=self.soccer_config)
            player_model_path = "./models/players.pt"
            keypoint_model_path = "./models/keypoints.pt"
            ball_model_path = "./models/ball.pt"
            self.frame_processor.load_models(player_model_path, keypoint_model_path, ball_model_path)
            self.frame_annotator = FrameAnnotator()
        except Exception as e:
            error_msg = f"An error occurred while loading models: {e}\n\nMake sure the 'models' folder and .pt files are in the correct location."
            QMessageBox.critical(None, "Kritik Hata", error_msg)
            # import sys
            # sys.exit(1) # Uygulamayı kapatmak isteyebilirsiniz

    def set_user(self, uid):
        self.user_id = uid
        if hasattr(self, 'home_page') and self.home_page:
            self.home_page.welcome_label.setText(f"👋 Hello, User") # Kullanıcı adını gösterebilirsiniz

    def init_ui(self):
        self.setWindowTitle("Football Vision AI")
        self.setMinimumSize(1200, 800)
        
        # Ekran boyutunu al ve pencere boyutunu ayarla
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        
        # Ekran boyutunun %90'ını kullan ama minimum değerleri koru
        width = max(1200, int(screen_size.width() * 0.9))
        height = max(800, int(screen_size.height() * 0.9))
        
        self.resize(width, height)
        
        # Pencereyi ekranın ortasına yerleştir
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        self.move(x, y)
        
        self.setStyleSheet(SIMPLE_STYLES["main_window"])

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self._create_sidebar()

        self.content_stacked_widget = QStackedWidget()
        self.content_stacked_widget.setStyleSheet("background-color: #2F3136;")

        self.home_page = HomePageWidget(self.frame_processor, self.frame_annotator)
        self.my_videos_page = MyVideosPage()
        self.analysis_results_page = AnalysisResultsPage()


        self.content_stacked_widget.addWidget(self.home_page)
        self.content_stacked_widget.addWidget(self.my_videos_page)
        self.content_stacked_widget.addWidget(self.analysis_results_page)
 
        
        self.my_videos_page.video_selected_for_processing.connect(self.handle_video_selection_for_processing)
        self.home_page.video_processed.connect(self.handle_video_processed)

        content_scroll_area = QScrollArea()
        content_scroll_area.setWidgetResizable(True)
        content_scroll_area.setStyleSheet(SIMPLE_STYLES["scroll_area"])
        content_scroll_area.setWidget(self.content_stacked_widget)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_scroll_area, 1)

        self.current_active_button = None
        self._set_active_sidebar_button(self.findChild(QPushButton, "Home Page"))

    def _create_sidebar(self):
        sidebar = QFrame()
        # Sidebar için özel stil - responsive height
        sidebar_style = SIMPLE_STYLES["sidebar"] + """
            QFrame {
                min-height: 600px; /* Minimum yükseklik artırıldı */
            }
        """
        sidebar.setStyleSheet(sidebar_style)
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)  # Alt margin eklendi
        sidebar_layout.setSpacing(3)  # Spacing azaltıldı

        # Menu butonları
        menu_items = ["Home Page", "Your Videos", "Transformed\nVideos"]  # Alt satıra geçirmek için \n eklendi
        self.sidebar_buttons = {}

        for i, item in enumerate(menu_items):
            btn = QPushButton(item)
            btn.setObjectName(item.replace('\n', ' '))  # Object name için \n kaldırıldı
            
            # Özel stil - çok satırlı metin için responsive
            multiline_style = SIMPLE_STYLES["sidebar_item"] + """
                QPushButton {
                    height: 55px; /* Yükseklik biraz azaltıldı */
                    text-align: center;
                    line-height: 1.2;
                    font-size: 16px; /* Font boyutu artırıldı */
                    padding: 8px 12px; /* Padding azaltıldı */
                    margin-bottom: 2px;
                }
            """
            btn.setStyleSheet(multiline_style)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons[item.replace('\n', ' ')] = btn  # Dictionary key için \n kaldırıldı

        # Esnek boşluk - logout butonunu alta itmek için ama daha az
        sidebar_layout.addStretch(1)
        
        # Logout butonu için boşluk
        sidebar_layout.addSpacing(10)  # Sabit boşluk eklendi
        
        # Logout butonu
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet(SIMPLE_STYLES["quit_button"] + """
            QPushButton {
                height: 45px;
                font-size: 15px; /* Font boyutu artırıldı */
                font-weight: bold;
                margin-bottom: 30px; /* Alt margin eklendi */
            }
        """)
        logout_btn.clicked.connect(self.logout)
        sidebar_layout.addWidget(logout_btn)
        
        return sidebar

    def _set_active_sidebar_button(self, button):
        if self.current_active_button:
            self.current_active_button.setChecked(False)
            # Multiline butonlar için özel stil
            multiline_style = SIMPLE_STYLES["sidebar_item"] + """
                QPushButton {
                    height: 55px;
                    text-align: center;
                    line-height: 1.2;
                    font-size: 16px;
                    padding: 8px 12px;
                    margin-bottom: 2px;
                }
            """
            self.current_active_button.setStyleSheet(multiline_style) # Normal stil
        button.setChecked(True)
        # Aktif buton için özel stil
        active_multiline_style = SIMPLE_STYLES["sidebar_item"] + SIMPLE_STYLES["sidebar_item_active"] + """
            QPushButton {
                height: 55px;
                text-align: center;
                line-height: 1.2;
                font-size: 16px;
                padding: 8px 12px;
                margin-bottom: 2px;
            }
        """
        button.setStyleSheet(active_multiline_style) # Aktif stil
        self.current_active_button = button

    def switch_page(self, index):
        menu_items = ["Home Page", "Your Videos", "Transformed Videos"]  # Normal isimler
        if index < len(menu_items):
            button_name = menu_items[index]
            if button_name in self.sidebar_buttons:
                self._set_active_sidebar_button(self.sidebar_buttons[button_name])
            self.content_stacked_widget.setCurrentIndex(index)
            
            if index == 1: # "Your Videos" sayfası
                self.my_videos_page.load_videos()
            elif index == 2: # "Transformed Videos" sayfası
                self.analysis_results_page.load_results()

    def handle_video_selection_for_processing(self, video_path):
        self.home_page.set_video_for_processing(video_path)
        self.switch_page(0) # Home Page'ya dön

    def handle_video_processed(self, video_path):
        print(f"Video işlendi: {video_path}. Transformed Videos sayfası güncellenebilir.")
        self.analysis_results_page.load_results() # Sonuçlar sayfasını yenilemek için çağrı

    def logout(self):
        # Ask for confirmation before logging out
        reply = QMessageBox.question(self, 'Logout Confirmation', 
                                     "Are you sure you want to log out?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.logout_callback:
                self.logout_callback()