# pages/analysis_results_page.py
import os
import cv2
import subprocess
import platform
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout, QHBoxLayout, QMessageBox 
from PyQt5.QtGui import QCursor, QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer

from ui.styles import SIMPLE_STYLES

class AnalysisResultsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #2F3136; color: white;")
        self.loading_label = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Transformed Video")
        title.setStyleSheet("font-weight: bold; color: white; font-size: 18px;")
        main_layout.addWidget(title)

        self.results_scroll_area = QScrollArea()
        self.results_scroll_area.setWidgetResizable(True)
        self.results_scroll_area.setStyleSheet(SIMPLE_STYLES["scroll_area"])

        self.results_content = QWidget()
        self.results_grid_layout = QGridLayout(self.results_content)
        self.results_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.results_scroll_area.setWidget(self.results_content)
        
                # Loading label ekleme
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
        main_layout.addWidget(self.results_scroll_area, 1)
        main_layout.addStretch(0)

        # CHANGE HERE: Add the scroll area with a stretch factor
        main_layout.addWidget(self.results_scroll_area, 1) # Gives the scroll area a stretch factor of 1
        main_layout.addStretch(0) # You can keep this or remove it

    def _update_loading_text(self):
        self.loading_dots = (self.loading_dots + 1) % 4
        dots = "." * self.loading_dots
        self.loading_label.setText(f"Loading{dots}")

    def show_loading(self):
        self.loading_label.show()
        self.loading_timer.start(500)
        self.results_scroll_area.hide()

    def hide_loading(self):
        self.loading_label.hide()
        self.loading_timer.stop()
        self.results_scroll_area.show()

    def load_results(self):
        self.show_loading()
        
        while self.results_grid_layout.count():
            child = self.results_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        outputs_folder = os.path.join(os.getcwd(), "outputs")
        os.makedirs(outputs_folder, exist_ok=True)
        
        result_files = [f for f in os.listdir(outputs_folder) 
                    if f.lower().endswith(('.mp4', '.avi'))]

        if not result_files:
            no_results_label = QLabel("There are no analysis results in the 'outputs' folder yet.\nThe results will appear here once the video processing is complete.")
            no_results_label.setStyleSheet("color: #BBBBBB; font-size: 14px;")
            no_results_label.setAlignment(Qt.AlignCenter)
            no_results_label.setWordWrap(True)
            self.results_grid_layout.addWidget(no_results_label, 0, 0, 1, -1, Qt.AlignCenter)
            self.hide_loading()
            return

        # Sonuçları aşamalı olarak yükle
        self.remaining_results = result_files.copy()
        self.current_index = 0
        QTimer.singleShot(100, self._load_next_result)

    def _load_next_result(self):
        if not self.remaining_results:
            self.hide_loading()
            return

        result_file = self.remaining_results.pop(0)
        result_path = os.path.join(os.getcwd(), "outputs", result_file)
        self._add_result_thumbnail(result_path, self.current_index)
        self.current_index += 1

        # Sonraki sonuç için zamanlayıcı ayarla
        QTimer.singleShot(100, self._load_next_result)

    def _add_result_thumbnail(self, result_path, index):
        thumbnail_card = QFrame()
        thumbnail_card.setStyleSheet(SIMPLE_STYLES["thumbnail_card"])
        thumbnail_layout = QVBoxLayout(thumbnail_card)
        thumbnail_layout.setContentsMargins(10, 10, 10, 10)
        thumbnail_layout.setSpacing(10)
        
        cap = cv2.VideoCapture(result_path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                qimage = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage).scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumbnail_label = QLabel()
                thumbnail_label.setPixmap(pixmap)
                thumbnail_label.setAlignment(Qt.AlignCenter)
                thumbnail_label.setStyleSheet("border: 1px solid #444;")
                thumbnail_layout.addWidget(thumbnail_label)
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes:02d}:{seconds:02d}"
                
                # Boyut ve süre bilgisini aynı etikette göster
                info_label = QLabel(f"Duration: {duration_text}")
                info_label.setStyleSheet("color: #BBBBBB; font-size: 10px;")
                info_label.setAlignment(Qt.AlignCenter)
                thumbnail_layout.addWidget(info_label)
                
            cap.release()
        else:
            thumbnail_label = QLabel("🎥")
            thumbnail_label.setStyleSheet("font-size: 50px; color: #666;")
            thumbnail_label.setAlignment(Qt.AlignCenter)
            thumbnail_layout.addWidget(thumbnail_label)

        file_name_label = QLabel(os.path.basename(result_path))
        file_name_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        file_name_label.setWordWrap(True)
        file_name_label.setAlignment(Qt.AlignCenter)
        thumbnail_layout.addWidget(file_name_label)
        
        file_size = os.path.getsize(result_path)
        file_size_mb = file_size / (1024 * 1024)
        info_label = QLabel(f"Size: {file_size_mb:.1f} MB")
        info_label.setStyleSheet("color: #BBBBBB; font-size: 10px;")
        info_label.setAlignment(Qt.AlignCenter)
        thumbnail_layout.addWidget(info_label)
        
        button_layout = QVBoxLayout()
        
        play_btn = QPushButton("Play Video")
        play_btn.setStyleSheet(SIMPLE_STYLES["button_primary"])
        play_btn.setCursor(QCursor(Qt.PointingHandCursor))
        play_btn.clicked.connect(lambda: self.play_video(result_path))
        
        open_folder_btn = QPushButton("Show in Folder")
        open_folder_btn.setStyleSheet(SIMPLE_STYLES["secondary_button"])
        open_folder_btn.setCursor(QCursor(Qt.PointingHandCursor))
        open_folder_btn.clicked.connect(lambda: self.open_in_folder(result_path))
        
        button_layout.addWidget(play_btn)
        button_layout.addWidget(open_folder_btn)
        thumbnail_layout.addLayout(button_layout)
        
        # Sayfanın genişliğini al
        viewport_width = self.results_scroll_area.viewport().width()
        
        # Bir thumbnail kartının genişliği (margin ve padding dahil)
        thumbnail_width = 220  # 200px thumbnail + 20px margins
        
        # Bir satıra sığabilecek thumbnail sayısını hesapla
        columns = max(1, viewport_width // thumbnail_width)
        
        # Satır ve sütun indekslerini hesapla
        row = index // columns
        col = index % columns
        
        self.results_grid_layout.addWidget(thumbnail_card, row, col)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Sayfa yeniden boyutlandırıldığında sonuçları tekrar yükle
        if hasattr(self, 'remaining_results'):
            self.load_results()

    def play_video(self, video_path):
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                os.startfile(video_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", video_path])
            else:
                subprocess.run(["xdg-open", video_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"The video could not be opened: {str(e)}")

    def open_in_folder(self, file_path):
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", file_path])
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", file_path])
            else:
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"The folder could not be opened: {str(e)}")