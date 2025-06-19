# workers/processing_worker.py
import os
import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

class ProcessingWorker(QObject):
    progress = pyqtSignal(int, int, int)  # percentage, current_frame, total_frames
    frame_preview_ready = pyqtSignal(object, object) # annotated_frame, radar_frame
    finished = pyqtSignal(list) # List of processed frame info dictionaries
    error = pyqtSignal(str)

    def __init__(self, video_processor, temp_dir, parent=None):
        super().__init__(parent)
        self.video_processor = video_processor
        self.temp_frame_dir = temp_dir
        self.is_running = True

    def run(self):
        processed_frames_info = []
        if not self.video_processor.setup_video_io():
            self.error.emit("Video dosyası açılamadı veya I/O hatası oluştu.")
            return

        total_frames = self.video_processor.total_frames
        
        for frame_count, (ret, frame) in enumerate(iter(lambda: self.video_processor.cap.read(), (False, None))):
            if not ret or not self.is_running:
                break
            
            try:
                annotated, radar = self.video_processor.process_frame(frame)
                
                if frame_count % 5 == 0: # Her 5 karede bir önizleme gönder
                    self.frame_preview_ready.emit(annotated, radar)

                annotated_path = os.path.join(self.temp_frame_dir, f"annotated_{frame_count:05d}.jpg")
                radar_path = os.path.join(self.temp_frame_dir, f"radar_{frame_count:05d}.jpg")
                cv2.imwrite(annotated_path, annotated)
                cv2.imwrite(radar_path, radar)
                
                processed_frames_info.append({
                    "annotated_path": annotated_path,
                    "radar_path": radar_path,
                    "selected": True
                })

            except Exception as e:
                print(f"Hata oluşan çerçeve {frame_count}: {e}")
            
            percent = int((frame_count + 1) / total_frames * 100)
            self.progress.emit(percent, frame_count + 1, total_frames)
        
        self.video_processor.cap.release()
        if self.is_running:
            self.finished.emit(processed_frames_info)

    def stop(self):
        self.is_running = False