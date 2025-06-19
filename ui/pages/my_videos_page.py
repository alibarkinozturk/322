# pages/my_videos_page.py
import os
import cv2
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout)
from PyQt5.QtGui import QCursor, QPixmap, QImage, QMovie
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from ui.styles import SIMPLE_STYLES

class MyVideosPage(QWidget):
    video_selected_for_processing = pyqtSignal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #2F3136; color: white;")
        self.loading_label = None
        self.init_ui()
        # load_videos burada çağrılmamalı, çünkü her sayfa geçişinde refresh olması istenir
        # init_ui sonrasında load_videos yerine, dashboard_window'da switch_page'den çağrılmalı

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Your Videos")
        title.setStyleSheet("font-weight: bold; color: white; font-size: 18px;")
        main_layout.addWidget(title)

        self.videos_scroll_area = QScrollArea()
        self.videos_scroll_area.setWidgetResizable(True)
        self.videos_scroll_area.setStyleSheet(SIMPLE_STYLES["scroll_area"])
        self.videos_content = QWidget()
        self.videos_grid_layout = QGridLayout(self.videos_content)
        self.videos_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.videos_scroll_area.setWidget(self.videos_content)

        self.loading_label = QLabel("Loading...")
        self.loading_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            padding: 20px;
            background-color: #36393f;
            border-radius: 8px;
        """)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()
        
        # Loading animasyonu için timer
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._update_loading_text)
        self.loading_dots = 0
        
        main_layout.addWidget(self.loading_label)
        
        # CHANGE HERE: Add the scroll area with a stretch factor
        main_layout.addWidget(self.videos_scroll_area, 1) # Gives the scroll area a stretch factor of 1
        main_layout.addStretch(0) 

    def _update_loading_text(self):
        self.loading_dots = (self.loading_dots + 1) % 4
        dots = "." * self.loading_dots
        self.loading_label.setText(f"Loading{dots}")

    def show_loading(self):
        self.loading_label.show()
        self.loading_timer.start(500)  # Her 500ms'de bir nokta güncellenecek
        self.videos_scroll_area.hide()

    def hide_loading(self):
        self.loading_label.hide()
        self.loading_timer.stop()
        self.videos_scroll_area.show()

    def load_videos(self):
        self.show_loading()
        
        # Mevcut video thumbnaillerini temizle
        while self.videos_grid_layout.count():
            child = self.videos_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        videos_folder = os.path.join(os.getcwd(), "videos")
        os.makedirs(videos_folder, exist_ok=True)
        video_files = [f for f in os.listdir(videos_folder) if f.lower().endswith(('.mp4', '.avi'))]

        if not video_files:
            no_videos_label = QLabel("There are no videos in the 'videos' folder yet.")
            no_videos_label.setStyleSheet("color: #BBBBBB;")
            self.videos_grid_layout.addWidget(no_videos_label, 0, 0, 1, -1, Qt.AlignCenter)
            self.hide_loading()
            return

        # Video thumbnaillerini yüklemek için QTimer kullan
        self.remaining_videos = video_files.copy()
        self.current_index = 0
        QTimer.singleShot(100, self._load_next_video)

    def _load_next_video(self):
        if not self.remaining_videos:
            self.hide_loading()
            return

        video_file = self.remaining_videos.pop(0)
        video_path = os.path.join(os.getcwd(), "videos", video_file)
        self._add_video_thumbnail(video_path, self.current_index)
        self.current_index += 1

        # Sonraki video için zamanlayıcı ayarla
        QTimer.singleShot(100, self._load_next_video)

    def _add_video_thumbnail(self, video_path, index):
        thumbnail_card = QFrame()
        thumbnail_card.setStyleSheet(SIMPLE_STYLES["thumbnail_card"])
        thumbnail_layout = QVBoxLayout(thumbnail_card)
        cap = cv2.VideoCapture(video_path)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                qimage = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage).scaled(200, 120, Qt.KeepAspectRatio)
                thumbnail_label = QLabel()
                thumbnail_label.setPixmap(pixmap)
                thumbnail_label.setAlignment(Qt.AlignCenter)
                thumbnail_layout.addWidget(thumbnail_label)
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes:02d}:{seconds:02d}"
                
                # Süre etiketini oluştur
                duration_label = QLabel(f"Duration: {duration_text}")
                duration_label.setStyleSheet("color: #BBBBBB; font-size: 10px;")
                duration_label.setAlignment(Qt.AlignCenter)
                thumbnail_layout.addWidget(duration_label)
            cap.release()
        else:
            thumbnail_label = QLabel("🎥")
            thumbnail_label.setStyleSheet("font-size: 50px;")
            thumbnail_label.setAlignment(Qt.AlignCenter)
            thumbnail_layout.addWidget(thumbnail_label)

        file_name_label = QLabel(os.path.basename(video_path))
        file_name_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        file_name_label.setWordWrap(True)
        file_name_label.setAlignment(Qt.AlignCenter)
        thumbnail_layout.addWidget(file_name_label)
        process_btn = QPushButton("Process This Video")
        process_btn.setStyleSheet(SIMPLE_STYLES["secondary_button"])
        process_btn.setCursor(QCursor(Qt.PointingHandCursor))
        process_btn.clicked.connect(lambda: self.video_selected_for_processing.emit(video_path))
        thumbnail_layout.addWidget(process_btn)
        
        viewport_width = self.videos_scroll_area.viewport().width()
        thumbnail_width = 220  # 200px thumbnail + 20px margins
        columns = max(1, viewport_width // thumbnail_width)
        row = index // columns
        col = index % columns
        self.videos_grid_layout.addWidget(thumbnail_card, row, col)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Sayfa yeniden boyutlandırıldığında videoları tekrar yükle
        if hasattr(self, 'remaining_videos'):
            self.load_videos()