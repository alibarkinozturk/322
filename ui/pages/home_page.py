import os
import shutil
import cv2
import subprocess
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout,
    QScrollArea, QGridLayout, QFileDialog, QProgressBar,
    QRadioButton, QButtonGroup, QMessageBox, QCheckBox, QSizePolicy,
    QApplication
)

from PyQt5.QtGui import QCursor, QPixmap, QImage, QFont, QDesktopServices 
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QDateTime, QUrl, QSize

from workers.processing_worker import ProcessingWorker
from utils.backend import FrameProcessor, FrameAnnotator, VideoProcessor
from ui.styles import SIMPLE_STYLES

class HomePageWidget(QWidget):
    video_processed = pyqtSignal(str) 

    def __init__(self, frame_processor, frame_annotator, parent=None):
        super().__init__(parent)
        self.frame_processor = frame_processor
        self.frame_annotator = frame_annotator
        
        self.setStyleSheet("background-color: #2F3136; color: white;")
        self.current_video_path = None
        self.temp_frame_dir = None
        self.processed_frames_info = []
        
        # Responsive değişkenler
        self.screen_size = QApplication.primaryScreen().size()
        self.is_small_screen = self.screen_size.width() < 1400 or self.screen_size.height() < 900
        
        self.init_ui()

    def get_responsive_sizes(self):
        """Ekran boyutuna göre responsive boyutları hesapla"""
        screen_width = self.screen_size.width()
        screen_height = self.screen_size.height()
        
        if screen_width < 1200:  # Küçük ekran
            return {
                'preview_width': 380,
                'preview_height': 250,
                'preview_container_width': 400,
                'preview_container_height': 320,
                'preview_spacing': 20,
                'card_width': 320,
                'card_height': 280,
                'thumb_width': 280,
                'thumb_height': 180,
                'grid_cols': 2
            }
        elif screen_width < 1600:  # Orta ekran
            return {
                'preview_width': 480,
                'preview_height': 320,
                'preview_container_width': 520,
                'preview_container_height': 400,
                'preview_spacing': 30,
                'card_width': 350,
                'card_height': 320,
                'thumb_width': 320,
                'thumb_height': 220,
                'grid_cols': 3
            }
        else:  # Büyük ekran
            return {
                'preview_width': 600,
                'preview_height': 380,
                'preview_container_width': 640,
                'preview_container_height': 480,
                'preview_spacing': 40,
                'card_width': 380,
                'card_height': 350,
                'thumb_width': 350,
                'thumb_height': 240,
                'grid_cols': 3
            }

    def init_ui(self):
        # Create a widget to hold all the content
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.header = self._create_header()
        self.upload_area = self._create_upload_area()
        self.output_selection_frame = self._create_output_selection_area()

        main_layout.addWidget(self.header)
        main_layout.addWidget(self.upload_area)
        main_layout.addWidget(self.output_selection_frame)
        
        self.start_process_btn = QPushButton("Start Transformation")
        self.start_process_btn.setStyleSheet(SIMPLE_STYLES["button_primary"])
        self.start_process_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.start_process_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.start_process_btn.clicked.connect(self.start_processing)
        self.start_process_btn.setEnabled(False)
        main_layout.addWidget(self.start_process_btn)

        self.progress_frame = self._create_progress_display()
        self.progress_frame.setVisible(False)
        main_layout.addWidget(self.progress_frame)
        
        self.post_process_frame = self._create_post_processing_ui()
        self.post_process_frame.setVisible(False)
        main_layout.addWidget(self.post_process_frame)

        self.final_video_frame = self._create_final_video_display()
        self.final_video_frame.setVisible(False)
        main_layout.addWidget(self.final_video_frame)

        main_layout.addStretch(1)

        # Create the scroll area and set the content_widget as its widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        scroll_area.setStyleSheet(SIMPLE_STYLES["scroll_area"])

        # Set the scroll area as the main widget of HomePageWidget
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_area)

    def _create_header(self):
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.welcome_label = QLabel("👋 Hello, User")
        self.welcome_label.setStyleSheet(SIMPLE_STYLES["header_text"])
        header_layout.addWidget(self.welcome_label)
        help_btn = QPushButton("Contact us for help")
        help_btn.setStyleSheet(SIMPLE_STYLES["secondary_button"])
        help_btn.clicked.connect(self.open_help_email)
        header_layout.addWidget(help_btn)
        return header
    
    def open_help_email(self):
        """Açılan mail taslağı ile varsayılan mail uygulamasını açar."""
        recipient = "abarkin.ozturk@tedu.edu.tr"
        subject = "322 - Request for Help"
        body = "Hello, I need help with application 322. Error:"
        
        # Create a mailto URI
        mailto_url = f"mailto:{recipient}?subject={subject}&body={body}"
        
        try:
            # Attempt to open the URL with the default application
            if not QDesktopServices.openUrl(QUrl(mailto_url)):
                # If opening failed (e.g., no default mail client configured)
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Could not open default mail application.\n"
                    f"Please manually open Outlook or your preferred email application and send an email with the following information:\n\n"
                    f"Receiver: {recipient}\n"
                    f"Subject: {subject}\n\n"
                    f"Content:\n{body}"
                )
        except Exception as e:
            # Catch any unexpected Python errors during the process
            QMessageBox.critical(
                self, 
                "Error", 
                f"An unexpected error occurred while opening the Mail app: {str(e)}\n\n"
                f"Please manually open Outlook or your preferred email application and send the email:\n"
                f"Receiver: {recipient}\n"
                f"Subject: {subject}"
            )

    def _create_upload_area(self):
        upload_area = QFrame()
        upload_area.setStyleSheet(SIMPLE_STYLES["card"])
        upload_layout = QVBoxLayout(upload_area)
        upload_title = QLabel("Select Video for Transformation")
        upload_title.setStyleSheet("font-weight: bold; color: white;")
        upload_layout.addWidget(upload_title)
        self.upload_btn = QPushButton("Click or Drag File Here for Video Upload\nUpload video in MP4 or AVI format (Max. 1GB)")
        self.upload_btn.setStyleSheet(SIMPLE_STYLES["upload_area"])
        self.upload_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.upload_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.upload_btn.clicked.connect(self.open_file_dialog)
        upload_layout.addWidget(self.upload_btn)
        return upload_area

    def _create_output_selection_area(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #36393F;
                border-radius: 12px;
                border: 1px solid #444444;
                padding: 20px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        
        # Başlık
        self.output_title = QLabel("Output Options")
        self.output_title.setStyleSheet("""
            font-weight: bold; 
            color: #4CAF50; 
            font-size: 18px;
            margin-bottom: 5px;
        """)
        layout.addWidget(self.output_title)
        
        # Radio butonları için özel stil
        radio_style = """
            QRadioButton {
                color: white;
                font-size: 15px;
                font-weight: 500;
                padding: 10px 16px;
                background-color: #2F3136;
                border: 2px solid #444444;
                border-radius: 8px;
                margin: 2px 0px;
                spacing: 8px;
            }
            QRadioButton:hover {
                background-color: #32353A;
                border-color: #4CAF50;
            }
            QRadioButton:checked {
                background-color: rgba(76, 175, 80, 0.2);
                border-color: #4CAF50;
                color: #4CAF50;
                font-weight: bold;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #666666;
                background-color: transparent;
                margin-right: 12px;
            }
            QRadioButton::indicator:hover {
                border-color: #4CAF50;
            }
            QRadioButton::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QRadioButton::indicator:checked:hover {
                background-color: #66BB6A;
            }
        """
        
        self.output_group = QButtonGroup(self)
        
        # Radio butonları
        self.radio_integrated = QRadioButton("🎬 Integrated Video (Original + Radar)")
        self.radio_integrated.setStyleSheet(radio_style)
        self.radio_integrated.setChecked(True)
        
        self.radio_annotated_only = QRadioButton("📝 Annotated Video Only")
        self.radio_annotated_only.setStyleSheet(radio_style)
        
        self.radio_radar_only = QRadioButton("📡 Radar Video Only")
        self.radio_radar_only.setStyleSheet(radio_style)
        
        # Butonları gruba ekle
        for radio in [self.radio_integrated, self.radio_annotated_only, self.radio_radar_only]:
            self.output_group.addButton(radio)
            layout.addWidget(radio)
        
        return frame

    def _create_progress_display(self):
        frame = QFrame()
        frame.setStyleSheet(SIMPLE_STYLES["card"])
        
        # Ana layout
        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # Üst kısım - Progress bilgileri
        progress_section = QVBoxLayout()
        progress_section.setSpacing(15)
        
        self.progress_label = QLabel("Video Transforming - Please Wait...")
        self.progress_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        self.progress_label.setAlignment(Qt.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(SIMPLE_STYLES["progress_bar"])
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(25)
        
        self.frame_progress_label = QLabel("Frame Processing: -")
        self.frame_progress_label.setStyleSheet("color: #BBBBBB; font-size: 14px;")
        self.frame_progress_label.setAlignment(Qt.AlignCenter)
        
        progress_section.addWidget(self.progress_label)
        progress_section.addWidget(self.progress_bar)
        progress_section.addWidget(self.frame_progress_label)
        
        main_layout.addLayout(progress_section)
        
        # Orta kısım - Önizleme başlığı
        preview_title = QLabel("📺 Live Preview")
        preview_title.setStyleSheet("color: #4CAF50; font-size: 16px; font-weight: bold;")
        preview_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(preview_title)
        
        # Responsive boyutları al
        sizes = self.get_responsive_sizes()
        
        # Önizleme bölümü - Responsive layout
        if self.is_small_screen:
            # Küçük ekranda dikey (VBox) layout
            preview_layout = QVBoxLayout()
            preview_layout.setSpacing(20)
            preview_layout.setContentsMargins(0, 0, 0, 0)
        else:
            # Büyük ekranda yatay (HBox) layout
            preview_layout = QHBoxLayout()
            preview_layout.setSpacing(sizes['preview_spacing'])
            preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sol önizleme - Responsive boyutlar
        left_container = QWidget()
        left_container.setFixedSize(sizes['preview_container_width'], sizes['preview_container_height'])
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        self.annotated_title = QLabel("🎬 Annotated")
        self.annotated_title.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: bold;")
        self.annotated_title.setAlignment(Qt.AlignCenter)
        
        self.annotated_preview_label = QLabel("Waiting...")
        self.annotated_preview_label.setFixedSize(sizes['preview_width'], sizes['preview_height'])
        self.annotated_preview_label.setAlignment(Qt.AlignCenter)
        self.annotated_preview_label.setStyleSheet("""
            border: 2px solid #4CAF50;
            background-color: #2A2A2A;
            border-radius: 8px;
            color: #888;
        """)
        self.annotated_preview_label.setScaledContents(True)
        
        left_layout.addWidget(self.annotated_title)
        left_layout.addWidget(self.annotated_preview_label, alignment=Qt.AlignCenter)
        
        # Sağ önizleme - Responsive boyutlar
        right_container = QWidget()
        right_container.setFixedSize(sizes['preview_container_width'], sizes['preview_container_height'])
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        self.radar_title = QLabel("📡 Radar")
        self.radar_title.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: bold;")
        self.radar_title.setAlignment(Qt.AlignCenter)
        
        self.radar_preview_label = QLabel("Waiting...")
        self.radar_preview_label.setFixedSize(sizes['preview_width'], sizes['preview_height'])
        self.radar_preview_label.setAlignment(Qt.AlignCenter)
        self.radar_preview_label.setStyleSheet("""
            border: 2px solid #4CAF50;
            background-color: #2A2A2A;
            border-radius: 8px;
            color: #888;
        """)
        self.radar_preview_label.setScaledContents(True)
        
        right_layout.addWidget(self.radar_title)
        right_layout.addWidget(self.radar_preview_label, alignment=Qt.AlignCenter)
        
        # Container'ları preview layout'a ekle - ortalanmış
        preview_layout.addStretch()
        preview_layout.addWidget(left_container, alignment=Qt.AlignCenter)
        if not self.is_small_screen:
            preview_layout.addStretch()
        preview_layout.addWidget(right_container, alignment=Qt.AlignCenter)
        preview_layout.addStretch()
        
        main_layout.addLayout(preview_layout)
        
        # Alt kısım - İptal butonu
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel Transformation")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5252;
                color: white;
                border-radius: 8px;
                padding: 12px 20px;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF1744;
            }
        """)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        return frame

    def _create_post_processing_ui(self):
        frame = QFrame()
        frame.setStyleSheet(SIMPLE_STYLES["card"])
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("🎬 Frame Selection and Video Creation")
        title.setStyleSheet("""
            font-weight: bold; 
            color: white; 
            font-size: 20px;
            padding: 15px;
            background-color: #4CAF50;
            border-radius: 10px;
            margin-bottom: 15px;
        """)
        layout.addWidget(title)
        
        description = QLabel("📌 Select the rendered frames you want and create the final video:")
        description.setStyleSheet("""
            color: #BBBBBB; 
            font-size: 16px;
            padding: 10px;
            margin-bottom: 20px;
        """)
        layout.addWidget(description)
        
        self.frame_banners_scroll_area = QScrollArea()
        self.frame_banners_scroll_area.setWidgetResizable(True)
        self.frame_banners_scroll_area.setStyleSheet(SIMPLE_STYLES["scroll_area"])
        
        # Responsive scroll area height ayarı
        if self.is_small_screen:
            self.frame_banners_scroll_area.setMinimumHeight(400)  # Küçük kartlar için daha az height
        else:
            self.frame_banners_scroll_area.setMinimumHeight(600)  # Orta/büyük kartlar için
        
        self.frame_banners_content = QWidget()
        self.frame_banners_layout = QGridLayout(self.frame_banners_content)
        self.frame_banners_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.frame_banners_layout.setSpacing(30)
        self.frame_banners_layout.setContentsMargins(25, 25, 25, 25)
        self.frame_banners_scroll_area.setWidget(self.frame_banners_content)
        
        layout.addWidget(self.frame_banners_scroll_area)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)
        
        self.selection_info_label = QLabel("All frames are selected")
        self.selection_info_label.setStyleSheet("""
            color: #4CAF50;
            font-size: 16px;
            font-weight: bold;
            padding: 12px;
            background-color: #2A2A2A;
            border-radius: 8px;
        """)
        button_layout.addWidget(self.selection_info_label)
        
        button_layout.addStretch()
        
        self.cancel_frame_selection_btn = QPushButton("Cancel Transformation")
        self.cancel_frame_selection_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5252;
                color: white;
                border-radius: 10px;
                padding: 15px 30px;
                border: none;
                font-size: 16px;
                font-weight: bold;
                min-width: 180px;
                margin-right: 15px;
            }
            QPushButton:hover {
                background-color: #FF1744;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """)
        self.cancel_frame_selection_btn.clicked.connect(self.cancel_frame_selection)
        button_layout.addWidget(self.cancel_frame_selection_btn)
        
        self.generate_final_video_btn = QPushButton("🎥 Create Final Video")
        self.generate_final_video_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                padding: 15px 30px;
                border: none;
                font-size: 18px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
        """)
        self.generate_final_video_btn.clicked.connect(self.generate_final_video)
        button_layout.addWidget(self.generate_final_video_btn)
        
        layout.addLayout(button_layout)
        return frame
    
    def cancel_frame_selection(self):
        reply = QMessageBox.question(
            self, 
            "Cancel Transformation", 
            "Are you sure you want to cancel the frame selection process?\n\nAll processed frames will be deleted and you will be returned to the home page.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.temp_frame_dir and os.path.exists(self.temp_frame_dir):
                try:
                    shutil.rmtree(self.temp_frame_dir)
                except Exception as e:
                    print(f"Geçici dosyalar silinirken hata: {e}")
            
            self._reset_ui_for_new_process()
            self._set_input_enabled(True)
            self.upload_btn.setText("Click or Drag File Here for Video Upload\nSelect video in MP4 or AVI format (Max. 1GB)")

    def _create_final_video_display(self):
        frame = QFrame()
        frame.setStyleSheet(SIMPLE_STYLES["card"])
        layout = QVBoxLayout(frame)
        title = QLabel("Created Video")
        title.setStyleSheet("font-weight: bold; color: white; font-size: 14px;")
        layout.addWidget(title)
        self.video_display_label = QLabel("Video başarıyla oluşturuldu!")
        self.video_display_label.setAlignment(Qt.AlignCenter)
        self.video_display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.video_display_label.setStyleSheet("border: 1px solid #333; background-color: black;")
        layout.addWidget(self.video_display_label)
        return frame

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi)")
        if file_path:
            self.set_video_for_processing(file_path)

    def set_video_for_processing(self, file_path):
        # Dosya uzantısı kontrolü
        allowed_extensions = {'.mp4', '.avi'}
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in allowed_extensions:
            QMessageBox.warning(
                self,
                "Invalid File Type",
                f"Only .mp4 and .avi files are supported.\nSelected file type: {file_extension}"
            )
            return

        # Dosya boyutu kontrolü (1GB = 1024*1024*1024 bytes)
        max_size = 1024 * 1024 * 1024  # 1GB
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            size_in_mb = file_size / (1024 * 1024)
            QMessageBox.warning(
                self,
                "File Too Large",
                f"Maximum file size is 1GB.\nSelected file size: {size_in_mb:.1f}MB"
            )
            return

        # Video dosyası açılabilirlik kontrolü
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            QMessageBox.warning(
                self,
                "Invalid Video File",
                "The selected file cannot be opened as a video file.\nPlease select a valid video file."
            )
            cap.release()
            return
        cap.release()

        # Tüm kontroller başarılı ise devam et
        self.current_video_path = file_path
        self.upload_btn.setText(f"Selected Video: {os.path.basename(file_path)}\n\nis Ready. You can start the transformation process.")
        self.start_process_btn.setEnabled(True)
        self._reset_ui_for_new_process()

    def _reset_ui_for_new_process(self):
        self.progress_frame.setVisible(False)
        self.post_process_frame.setVisible(False)
        self.final_video_frame.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Video Transforming - Plese Wait...")
        self.frame_progress_label.setText("Frame Processing: -")
        
        while self.frame_banners_layout.count():
            child = self.frame_banners_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if self.temp_frame_dir and os.path.exists(self.temp_frame_dir):
            shutil.rmtree(self.temp_frame_dir)
            self.temp_frame_dir = None
            

        if self.frame_processor:
            self.frame_processor.reset_state()
            
        self._set_input_enabled(True)

    def _set_input_enabled(self, enabled):
        self.header.setVisible(enabled)
        self.upload_area.setVisible(enabled)
        self.output_selection_frame.setVisible(enabled)
        self.start_process_btn.setVisible(enabled)
        if enabled:
            self.start_process_btn.setEnabled(bool(self.current_video_path))
        else:
            self.start_process_btn.setEnabled(False)

    def start_processing(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "Video Not Selected", "Please select a video to process first.")
            return

        self._set_input_enabled(False)
        self.progress_frame.setVisible(True)

        # --- YENİ EKLENEN SATIR ---
        # Her yeni işlemden önce FrameProcessor'ın durumunu sıfırla
        self.frame_processor.reset_state()
        # ---------------------------

        self.temp_frame_dir = f"temp_frames/run_{QDateTime.currentDateTime().toSecsSinceEpoch()}"
        os.makedirs(self.temp_frame_dir, exist_ok=True)
        
        video_processor_instance = VideoProcessor(
            self.current_video_path, "", self.frame_processor, self.frame_annotator
        )

        self.thread = QThread()
        self.worker = ProcessingWorker(video_processor_instance, self.temp_frame_dir)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.frame_preview_ready.connect(self.update_frame_previews)
        self.worker.error.connect(self.handle_processing_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_progress(self, percentage, current, total):
        self.progress_bar.setValue(percentage)
        self.frame_progress_label.setText(f"Frame Processing: {current}/{total}")

    def update_frame_previews(self, annotated_img, radar_img):
        """Önizleme görüntülerini güncelle - Responsive boyutlarla"""
        sizes = self.get_responsive_sizes()
        
        # Anotasyonlu görüntü
        if isinstance(annotated_img, np.ndarray):
            h, w, ch = annotated_img.shape
            q_img = QImage(annotated_img.data, w, h, ch * w, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_img).scaled(
                sizes['preview_width'], 
                sizes['preview_height'], 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.annotated_preview_label.setPixmap(pixmap)
        
        # Radar görüntüsü
        if isinstance(radar_img, np.ndarray):
            h, w, ch = radar_img.shape
            q_img = QImage(radar_img.data, w, h, ch * w, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_img).scaled(
                sizes['preview_width'], 
                sizes['preview_height'], 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.radar_preview_label.setPixmap(pixmap)

    def on_processing_finished(self, processed_frames_info):
        self.processed_frames_info = processed_frames_info
        self.progress_frame.setVisible(False)
        
        if not processed_frames_info:
            QMessageBox.warning(self, "Transform Completed", "The video was processed but no frames were saved. Please check the video.")
            self._reset_ui_for_new_process()
            self._set_input_enabled(True)
            return

        self.post_process_frame.setVisible(True)
        self.populate_frame_selection_grid()
        self.video_processed.emit(self.current_video_path)

    def handle_processing_error(self, error_message):
        QMessageBox.critical(self, "Process Error", error_message)
        self.cancel_processing()

    def cancel_processing(self):
        if hasattr(self, 'worker') and self.worker:
            self.worker.stop()
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        
        self._reset_ui_for_new_process()
        self._set_input_enabled(True)
        QMessageBox.information(self, "Cancelled", "The process was canceled by the user.")

    def populate_frame_selection_grid(self):
        """Kare seçimi grid'ini responsive olarak oluştur"""
        # Mevcut grid'i temizle
        while self.frame_banners_layout.count():
            child = self.frame_banners_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        sizes = self.get_responsive_sizes()
        cols = sizes['grid_cols']
        
        # Grid spacing'i responsive yap
        if self.is_small_screen:
            self.frame_banners_layout.setSpacing(20)
            self.frame_banners_layout.setContentsMargins(15, 15, 15, 15)
        else:
            self.frame_banners_layout.setSpacing(30)
            self.frame_banners_layout.setContentsMargins(25, 25, 25, 25)
        
        for i, info in enumerate(self.processed_frames_info):
            row, col = divmod(i, cols)
            
            frame_card = QFrame()
            frame_card_layout = QVBoxLayout(frame_card)
            
            # Responsive padding
            padding = 15 if self.is_small_screen else 20
            frame_card_layout.setContentsMargins(padding, padding, padding, padding)
            frame_card_layout.setSpacing(12 if self.is_small_screen else 15)
            
            # Responsive card styling
            frame_card.setStyleSheet(f"""
                QFrame {{ 
                    background-color: #36393F; 
                    border-radius: 15px; 
                    border: 3px solid #444444;
                    min-width: {sizes['card_width']}px;
                    min-height: {sizes['card_height']}px;
                    max-width: {sizes['card_width'] + 50}px;  
                    max-height: {sizes['card_height'] + 50}px; 
                }}
                QFrame:hover {{
                    border: 4px solid #4CAF50;
                    background-color: #3A3D42;
                }}
            """)
            # Thumbnail oluştur - responsive boyutlarla
            thumb_label = QLabel()
            pixmap = QPixmap(info["annotated_path"])
            scaled_pixmap = pixmap.scaled(
                sizes['thumb_width'], 
                sizes['thumb_height'], 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            thumb_label.setPixmap(scaled_pixmap)
            thumb_label.setAlignment(Qt.AlignCenter)
            
            # Responsive thumbnail styling
            thumb_label.setStyleSheet(f"""
                border: 3px solid #666; 
                border-radius: 10px;
                background-color: #2A2A2A;
                padding: 8px;
                min-height: {sizes['thumb_height']}px;
                min-width: {sizes['thumb_width']}px;
                max-height: {sizes['thumb_height'] + 20}px;
                max-width: {sizes['thumb_width'] + 20}px;
            """)
            
            # Checkbox oluştur - responsive styling
            checkbox = QCheckBox(f"🎯 Frame {i+1}")
            checkbox.setChecked(info["selected"])
            
            # Responsive checkbox font size ve padding
            if self.is_small_screen:
                checkbox_font_size = "14px"
                checkbox_padding = "10px"
                checkbox_height = "40px"
                indicator_size = "24px"
            else:
                checkbox_font_size = "18px"
                checkbox_padding = "15px"
                checkbox_height = "50px"
                indicator_size = "28px"
            
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: white;
                    font-weight: bold;
                    font-size: {checkbox_font_size};
                    padding: {checkbox_padding};
                    background-color: #2A2A2A;
                    border-radius: 10px;
                    min-height: {checkbox_height};
                }}
                QCheckBox::indicator {{
                    width: {indicator_size};
                    height: {indicator_size};
                    border-radius: 5px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: #4CAF50;
                    border: 4px solid #4CAF50;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjUgNEw2IDExLjUgMi41IDhMMSA5LjUgNiAxNC41IDE1IDIuNSAxMy41IDRaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K);
                }}
                QCheckBox::indicator:unchecked {{
                    background-color: #404040;
                    border: 4px solid #666;
                }}
                QCheckBox::indicator:hover {{
                    border: 4px solid #4CAF50;
                    background-color: #555;
                }}
            """)
            checkbox.toggled.connect(lambda state, index=i: self.update_frame_selection(state, index))

            # Widget'ları layout'a ekle
            frame_card_layout.addWidget(thumb_label)
            frame_card_layout.addWidget(checkbox, alignment=Qt.AlignCenter)

            # Frame card'ı grid'e ekle
            self.frame_banners_layout.addWidget(frame_card, row, col)
        
        # Grid'i yeniden düzenle
        self.frame_banners_content.updateGeometry()
        self.frame_banners_scroll_area.updateGeometry()

    def update_frame_selection(self, state, index):
        if 0 <= index < len(self.processed_frames_info):
            self.processed_frames_info[index]["selected"] = state
            
            selected_count = sum(1 for info in self.processed_frames_info if info["selected"])
            total_count = len(self.processed_frames_info)
            
            if hasattr(self, 'selection_info_label'):
                if selected_count == 0:
                    self.selection_info_label.setText("⚠️ No frames selected!")
                    self.selection_info_label.setStyleSheet("color: #FF5252; font-size: 14px; font-weight: bold; padding: 8px;")
                elif selected_count == total_count:
                    self.selection_info_label.setText("✅ All frames are selected")
                    self.selection_info_label.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: bold; padding: 8px;")
                else:
                    self.selection_info_label.setText(f"📊 {selected_count}/{total_count} frame selected")
                    self.selection_info_label.setStyleSheet("color: #FFC107; font-size: 14px; font-weight: bold; padding: 8px;")

    def generate_final_video(self):
        output_choice = "integrated"
        if self.radio_annotated_only.isChecked():
            output_choice = "annotated_only"
        elif self.radio_radar_only.isChecked():
            output_choice = "radar_only"

        output_filename_base = os.path.splitext(os.path.basename(self.current_video_path))[0]
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        final_video_path = os.path.join(output_dir, f"{output_filename_base}_{output_choice}.mp4")
        
        selected_infos = [info for info in self.processed_frames_info if info["selected"]]
        if not selected_infos:
            self.handle_processing_error("No frame selected. Cannot create video.")
            return

        cap = cv2.VideoCapture(self.current_video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
        cap.release()

        first_frame_path = selected_infos[0]["radar_path"] if output_choice == "radar_only" else selected_infos[0]["annotated_path"]
        first_frame = cv2.imread(first_frame_path)
        if first_frame is None:
            
            self.handle_processing_error(f"The first frame could not be taken:: {first_frame_path}")
            return
        height, width, _ = first_frame.shape

        writer = cv2.VideoWriter(final_video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        for info in selected_infos:
            frame_to_write = None
            if output_choice == "annotated_only":
                frame_to_write = cv2.imread(info["annotated_path"])
            elif output_choice == "radar_only":
                frame_to_write = cv2.imread(info["radar_path"])
            elif output_choice == "integrated":
                main_frame = cv2.imread(info["annotated_path"])
                radar_frame = cv2.imread(info["radar_path"])
                if main_frame is None or radar_frame is None: continue

                radar_h, radar_w, _ = radar_frame.shape
                new_radar_w = int(width * 0.2)
                new_radar_h = int(radar_h * (new_radar_w / radar_w))
                radar_small = cv2.resize(radar_frame, (new_radar_w, new_radar_h))
                
                y_offset = height - new_radar_h - 10
                x_offset = (width - new_radar_w) // 2
                
                main_frame[y_offset:y_offset+new_radar_h, x_offset:x_offset+new_radar_w] = radar_small
                frame_to_write = main_frame
            
            if frame_to_write is not None:
                writer.write(frame_to_write)
        
        writer.release()
        
        QMessageBox.information(self, "Successful", f"Video created successfully!\nLocation: {final_video_path}")
        self._reset_ui_for_new_process()
        self._set_input_enabled(True)
        self.upload_btn.setText("Select a new video...")
        self.video_processed.emit(final_video_path) # İşlem bitiminde sinyal gönder

    def resizeEvent(self, event):
        """Pencere boyutu değiştiğinde responsive güncelleme"""
        super().resizeEvent(event)
        
        # Yeni ekran boyutunu güncelle
        self.screen_size = self.size()
        old_is_small = self.is_small_screen
        self.is_small_screen = self.screen_size.width() < 1400 or self.screen_size.height() < 900
        
        # Eğer ekran boyutu kategorisi değiştiyse, UI'yi güncelle
        if old_is_small != self.is_small_screen:
            self._update_responsive_elements()
    
    def _update_responsive_elements(self):
        """Responsive element boyutlarını güncelle"""
        sizes = self.get_responsive_sizes()
        
        # Preview label boyutlarını güncelle
        if hasattr(self, 'annotated_preview_label') and hasattr(self, 'radar_preview_label'):
            self.annotated_preview_label.setFixedSize(sizes['preview_width'], sizes['preview_height'])
            self.radar_preview_label.setFixedSize(sizes['preview_width'], sizes['preview_height'])
            
            # Container boyutlarını güncelle
            if hasattr(self, 'annotated_preview_label'):
                parent = self.annotated_preview_label.parent()
                if parent:
                    parent.setFixedSize(sizes['preview_container_width'], sizes['preview_container_height'])
            
            if hasattr(self, 'radar_preview_label'):
                parent = self.radar_preview_label.parent()
                if parent:
                    parent.setFixedSize(sizes['preview_container_width'], sizes['preview_container_height'])
        
        # Scroll area height güncelle
        if hasattr(self, 'frame_banners_scroll_area'):
            if self.is_small_screen:
                self.frame_banners_scroll_area.setMinimumHeight(400)
            else:
                self.frame_banners_scroll_area.setMinimumHeight(600)
        
        # Eğer kare seçimi görünüyorsa, grid'i yeniden oluştur
        if hasattr(self, 'post_process_frame') and self.post_process_frame.isVisible():
            if hasattr(self, 'processed_frames_info') and self.processed_frames_info:
                self.populate_frame_selection_grid()