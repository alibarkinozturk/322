import cv2
import numpy as np
import torch
from ultralytics import YOLO
import supervision as sv
from sklearn.cluster import KMeans
from typing import List, Tuple, Dict, Optional
import collections
# Bu importlar kendi projenizdeki dosya yapılandırmanıza göre düzenlenmelidir.
from utils.config import SoccerPitchConfiguration
from utils.Draw import draw_points_on_pitch, draw_pitch, draw_paths_on_pitch
from utils.view import ViewTransformer
import concurrent.futures
# PyQt5 ve UI sınıfı için importlar (PyQt6'dan PyQt5'e değiştirildi)
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

# --- MODEL PATHS (Lütfen kendi model yollarınızla güncelleyin) ---
PLAYER_MODEL_PATH = "./models/players.pt"
KEYPOINT_MODEL_PATH = "./models/keypoints.pt"
BALL_MODEL_PATH = "./models/ball.pt"

class FrameAnnotator:
    """
    Handles the annotation of frames with various detections
    such as players, goalkeepers, referees, and the ball,
    including team-specific information and jersey analysis.
    """
    
    def __init__(self):

        self.ball_annotator = sv.CircleAnnotator(
            color=sv.Color.RED,
            thickness=2,
        )
        
        self.label_annotator = sv.LabelAnnotator(
            text_position=sv.Position.TOP_CENTER,
            text_scale=0.5,
            text_thickness=1,
            text_color=sv.Color.WHITE,
            text_padding=3,
        )

    def _annotate_with_dot_and_label(self, frame, detections, dot_color, label_prefix):
        if len(detections) > 0:
            dot_annotator = sv.DotAnnotator(color=dot_color, radius=8, position=sv.Position.BOTTOM_CENTER)
            frame = dot_annotator.annotate(scene=frame, detections=detections)
            if detections.tracker_id is not None:
                labels = [f"{label_prefix}:{tracker_id}" for tracker_id in detections.tracker_id]
                frame = self.label_annotator.annotate(scene=frame, detections=detections, labels=labels)
        return frame

    def annotate_players(self, frame: np.ndarray, player_detections: sv.Detections) -> np.ndarray:
        return self._annotate_with_dot_and_label(frame, player_detections, sv.Color.BLUE, "P")

    def annotate_goalkeepers(self, frame: np.ndarray, goalkeeper_detections: sv.Detections) -> np.ndarray:
        return self._annotate_with_dot_and_label(frame, goalkeeper_detections, sv.Color.GREEN, "GK")
    
    def annotate_referees(self, frame: np.ndarray, referee_detections: sv.Detections) -> np.ndarray:
        return self._annotate_with_dot_and_label(frame, referee_detections, sv.Color.YELLOW, "R")

    def annotate_ball(self, frame: np.ndarray, ball_detections: sv.Detections) -> np.ndarray:
        if len(ball_detections) == 1:
            frame = self.ball_annotator.annotate(scene=frame, detections=ball_detections)
            if ball_detections.tracker_id is not None:
                labels = [f"Ball:{tracker_id}" for tracker_id in ball_detections.tracker_id]
                ball_label_annotator = sv.LabelAnnotator(
                    text_position=sv.Position.BOTTOM_CENTER,
                    text_scale=0.1, text_thickness=1, text_color=sv.Color.WHITE, text_padding=2)
                frame = ball_label_annotator.annotate(scene=frame, detections=ball_detections, labels=labels)
        return frame

    def annotate_frame(self, frame: np.ndarray, detections: Dict[str, sv.Detections],
                       team_assignments: Optional[Dict[int, int]] = None,
                       team_centroids: Optional[Dict[int, np.ndarray]] = None,
                       show_jersey_regions: bool = True) -> np.ndarray:
        annotated_frame = frame.copy()

        if 'players' in detections and detections['players'] is not None:
            annotated_frame = self.annotate_players(annotated_frame, detections['players'])
            if show_jersey_regions and team_assignments is not None:
                annotated_frame = self.annotate_jersey_regions(
                    annotated_frame, detections['players'], team_assignments, team_centroids
                )

        if 'goalkeepers' in detections and detections['goalkeepers'] is not None:
            annotated_frame = self.annotate_goalkeepers(annotated_frame, detections['goalkeepers'])

        if 'referees' in detections and detections['referees'] is not None:
            annotated_frame = self.annotate_referees(annotated_frame, detections['referees'])

        if 'ball' in detections and detections['ball'] is not None:
            annotated_frame = self.annotate_ball(annotated_frame, detections['ball'])

        if team_centroids and show_jersey_regions:
            annotated_frame = self.annotate_team_info(annotated_frame, team_centroids)

        return annotated_frame

    def annotate_jersey_regions(self, frame: np.ndarray, player_detections: sv.Detections,
                                team_assignments: Dict[int, int],
                                team_centroids: Optional[Dict[int, np.ndarray]] = None) -> np.ndarray:

        if len(player_detections) == 0 or player_detections.tracker_id is None:
            return frame

        annotated_frame = frame.copy()
        team_display_colors = {}

        if team_centroids:
            for team_id, centroid_rgb in team_centroids.items():
                if centroid_rgb is not None:
                    team_display_colors[team_id] = (int(centroid_rgb[2]), int(centroid_rgb[1]), int(centroid_rgb[0]))

        if 0 not in team_display_colors:
            team_display_colors[0] = (255, 0, 0)

        if 1 not in team_display_colors:
            team_display_colors[1] = (0, 0, 255)

        team_display_colors[-1] = (255, 255, 255)

        for i in range(len(player_detections)):
            bbox = player_detections.xyxy[i]
            tracker_id = player_detections.tracker_id[i]
            x1, y1, x2, y2 = bbox.astype(int)
            height = y2 - y1
            width = x2 - x1
            jersey_y1 = y1 + int(height * 0.3)
            jersey_y2 = y1 + int(height * 0.55)
            jersey_x1 = x1 + int(width * 0.35)
            jersey_x2 = x1 + int(width * 0.65)
            jersey_y1 = np.clip(jersey_y1, 0, frame.shape[0] - 1)
            jersey_y2 = np.clip(jersey_y2, 0, frame.shape[0] - 1)
            jersey_x1 = np.clip(jersey_x1, 0, frame.shape[1] - 1)
            jersey_x2 = np.clip(jersey_x2, 0, frame.shape[1] - 1)
            team_id = team_assignments.get(tracker_id, -1)
            display_color_bgr = team_display_colors.get(team_id, (255, 255, 255))

            if jersey_y2 > jersey_y1 and jersey_x2 > jersey_x1:
                cv2.rectangle(annotated_frame, (jersey_x1, jersey_y1), (jersey_x2, jersey_y2), display_color_bgr, 2)

            label_text = f"T{team_id}" if team_id != -1 else "T?"

            if team_centroids and team_id in team_centroids and team_centroids[team_id] is not None:
                dominant_color_rgb = team_centroids[team_id]
                bgr_color_from_centroid = (
                    int(dominant_color_rgb[2]), int(dominant_color_rgb[1]), int(dominant_color_rgb[0]))
                color_rect_x1, color_rect_y1, color_rect_x2, color_rect_y2 = x1, jersey_y1 - 25, x1 + 20, jersey_y1 - 5

                if color_rect_y1 >= 0:
                    cv2.rectangle(annotated_frame, (color_rect_x1, color_rect_y1), (color_rect_x2, color_rect_y2),
                                  bgr_color_from_centroid, -1)

                    cv2.rectangle(annotated_frame, (color_rect_x1, color_rect_y1), (color_rect_x2, color_rect_y2),
                                  (0, 0, 0), 1)

                rgb_text = f"RGB({int(dominant_color_rgb[0])},{int(dominant_color_rgb[1])},{int(dominant_color_rgb[2])})"

                cv2.putText(annotated_frame, rgb_text, (x1, jersey_y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                            (255, 255, 255), 1)

            cv2.putText(annotated_frame, label_text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, display_color_bgr, 2)

        return annotated_frame

    def annotate_team_info(self, frame: np.ndarray, team_centroids: Dict[int, np.ndarray]) -> np.ndarray:

        if not team_centroids or (team_centroids.get(0) is None and team_centroids.get(1) is None):
            return frame

        annotated_frame = frame.copy()
        y_offset = 30

        for team_id, centroid_rgb in team_centroids.items():

            if centroid_rgb is not None:
                bgr_color = (int(centroid_rgb[2]), int(centroid_rgb[1]), int(centroid_rgb[0]))
                text = f"Team {team_id}:"
                cv2.putText(annotated_frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                color_rect_x1, color_rect_y1, color_rect_x2, color_rect_y2 = 120, y_offset - 20, 170, y_offset - 5
                cv2.rectangle(annotated_frame, (color_rect_x1, color_rect_y1), (color_rect_x2, color_rect_y2),
                              bgr_color, -1)
                cv2.rectangle(annotated_frame, (color_rect_x1, color_rect_y1), (color_rect_x2, color_rect_y2),
                              (0, 0, 0), 2)
                rgb_text = f"RGB({int(centroid_rgb[0])},{int(centroid_rgb[1])},{int(centroid_rgb[2])})"
                cv2.putText(annotated_frame, rgb_text, (180, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255),
                            1)
                y_offset += 40
                
        return annotated_frame


class FrameProcessor:

    def __init__(self, pitch_config: SoccerPitchConfiguration):
        self.pitch_config = pitch_config
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.player_model = None
        self.keypoint_model = None
        self.ball_model = None
        self.class_ids = {}
        self.player_tracker = sv.ByteTrack()
        self.goalkeeper_tracker = sv.ByteTrack()
        self.referee_tracker = sv.ByteTrack()
        self.ball_tracker = sv.ByteTrack()
        self.movement_history = {}
        self.path_history_length = 50
        self.team0_centroid = None
        self.team1_centroid = None
        self.team_colors_initialized = False
        self.player_team_assignments = {}
        self.last_seen_players = {}  # {tracker_id: {'bbox': ..., 'frame': ..., 'team': ...}}
        self.max_missing_frames = 20  # Kaç frame boyunca kaybolan oyuncu gösterilsin
        self.last_successful_transformer = None
        
    def reset_state(self):
        """
        İşlemci durumunu yeni bir video için sıfırlar.
        Bu, pozisyon geçmişini, takipçileri ve takım bilgilerini temizler.
        """
        print("FrameProcessor durumu sıfırlanıyor...")
        # Pozisyon yumuşatma geçmişini temizle
        self.position_history = collections.defaultdict(
            lambda: collections.deque(maxlen=self.smoothing_window_size)
        )
        
        # Takipçileri yeniden başlat
        self.player_tracker = sv.ByteTrack()
        self.goalkeeper_tracker = sv.ByteTrack()
        self.referee_tracker = sv.ByteTrack()
        self.ball_tracker = sv.ByteTrack()
        
        # Takım rengi ve atama bilgilerini temizle
        self.team0_centroid = None
        self.team1_centroid = None
        self.team_colors_initialized = False
        self.player_team_assignments = {}
        
        # Son görülme bilgilerini temizle
        self.last_seen_players = {}
        
        # Son başarılı transformer'ı da temizle
        self.last_successful_transformer = None
        
    def load_models(self, player_model_path, keypoint_model_path, ball_model_path):
        self.player_model = YOLO(player_model_path).to(self.device)
        self.keypoint_model = YOLO(keypoint_model_path).to(self.device)
        self.ball_model = YOLO(ball_model_path).to(self.device)
        
        if hasattr(self.player_model.model, 'names'):
            names = self.player_model.model.names
            self.class_ids = {k: v for v, k in names.items()}

    def detect_keypoints(self, frame: np.ndarray) -> Optional[ViewTransformer]:
        """
        Keypoint detection yapar. Eğer keypoint bulunamazsa son başarılı transformer'ı döner.
        """
        if not self.keypoint_model or not getattr(self.pitch_config, 'vertices', None):
            return self.last_successful_transformer

        results = self.keypoint_model(frame, conf=0.45, verbose=False)[0]

        if not hasattr(results, 'keypoints') or results.keypoints is None:
            print("Keypoints bulunamadı, son başarılı transformer kullanılıyor...")
            return self.last_successful_transformer

        sv_keypoints = sv.KeyPoints.from_ultralytics(results)

        if len(sv_keypoints.xy) == 0:
            print("Keypoint array boş, son başarılı transformer kullanılıyor...")
            return self.last_successful_transformer

        frame_pts = sv_keypoints.xy[0]
        conf = sv_keypoints.confidence[0] if sv_keypoints.confidence is not None else np.ones(len(frame_pts))
        mask = conf > 0.5
        filtered_pts = frame_pts[mask]
        pitch_pts = np.array(self.pitch_config.vertices, dtype=np.float32)[mask]

        if len(filtered_pts) < 4:
            print("Yeterli keypoint bulunamadı (< 4), son başarılı transformer kullanılıyor...")
            return self.last_successful_transformer

        try:
            # Yeni transformer oluştur
            new_transformer = ViewTransformer(source=filtered_pts, target=pitch_pts)
            # Başarılı olursa son başarılı transformer'ı güncelle
            self.last_successful_transformer = new_transformer
            print("Yeni keypoint transformer başarıyla oluşturuldu")
            return new_transformer

        except Exception as e:
            print(f"ViewTransformer oluşturulurken hata: {e}, son başarılı transformer kullanılıyor...")
            return self.last_successful_transformer

    def filter_referees_by_color(self, detections: sv.Detections, frame: np.ndarray) -> sv.Detections:
        # Takım renkleri henüz belirlenmediyse filtreleme yapma
        if self.team0_centroid is None or self.team1_centroid is None:
            return detections # Veya boş bir detection döndür: sv.Detections.empty()

        filtered_indices = []
        
        # Takım renklerini HSV uzayında karşılaştırmak genellikle daha iyi sonuç verir
        team0_hsv = cv2.cvtColor(np.uint8([[self.team0_centroid]]), cv2.COLOR_RGB2HSV)[0][0]
        team1_hsv = cv2.cvtColor(np.uint8([[self.team1_centroid]]), cv2.COLOR_RGB2HSV)[0][0]

        for i, bbox in enumerate(detections.xyxy):
            jersey = self._extract_jersey_region(frame, bbox)
            if jersey.size == 0: continue
            
            referee_color_rgb = self._compute_dominant_color(jersey)
            if referee_color_rgb is None: continue
            
            referee_color_hsv = cv2.cvtColor(np.uint8([[referee_color_rgb]]), cv2.COLOR_RGB2HSV)[0][0]
            
            # --- DÜZELTME BURADA ---
            # Çıkarma yapmadan önce değerleri standart 'int' tipine dönüştürüyoruz.
            # Bu, uint8'in neden olduğu overflow/underflow hatasını engeller.
            ref_h = int(referee_color_hsv[0])
            t0_h = int(team0_hsv[0])
            t1_h = int(team1_hsv[0])
            
            # Renkler arasındaki farkı hesapla (Örnek: sadece Hue (renk tonu) farkı)
            # Not: Hue dairesel olduğu için (0 ve 180 birbirine yakındır) farkı dikkatli hesaplamak gerekir.
            diff_to_team0 = min(abs(ref_h - t0_h), 180 - abs(ref_h - t0_h))
            diff_to_team1 = min(abs(ref_h - t1_h), 180 - abs(ref_h - t1_h))
            
            # Eğer hakem adayının rengi her iki takımın renginden de yeterince farklıysa, onu hakem olarak kabul et.
            # Bu eşik değerini (örn: 20) deneme yanılma ile bulabilirsiniz.
            if diff_to_team0 > 20 and diff_to_team1 > 20:
                filtered_indices.append(i)
                
        return detections[filtered_indices]

    def detect_objects(self, frame: np.ndarray) -> Dict[str, Optional[sv.Detections]]:

        results = {'players': None, 'goalkeepers': None, 'referees': None, 'ball': None}

        if self.player_model:
            dets = sv.Detections.from_ultralytics(self.player_model(frame, conf=0.45, verbose=False)[0])
            class_map = {v: k for k, v in self.player_model.model.names.items()}
            player_ids, goalkeeper_ids, referee_ids = [class_map.get('player', 0)], [class_map.get('goalkeeper', 1)], [
                class_map.get('referee', 2)]
            results['players'] = self.player_tracker.update_with_detections(
                dets[np.isin(dets.class_id, player_ids)].with_nms(threshold=0.3))
            if results['players'] is not None and results['players'].tracker_id is not None:

                for i, tracker_id in enumerate(results['players'].tracker_id):
                    self.last_seen_players[tracker_id] = {
                        'bbox': results['players'].xyxy[i].copy(),
                        'frame': 0,  # Şu anki frame'de görüldü
                        'team': self.player_team_assignments.get(tracker_id, -1)
                    }

            results['goalkeepers'] = self.goalkeeper_tracker.update_with_detections(
                dets[np.isin(dets.class_id, goalkeeper_ids)].with_nms(threshold=0.3))

            results['referees'] = self.filter_referees_by_color(self.referee_tracker.update_with_detections(
                dets[np.isin(dets.class_id, referee_ids)].with_nms(threshold=0.3)), frame)

        if self.ball_model:

            ball_dets = sv.Detections.from_ultralytics(self.ball_model(frame, conf=0.1, verbose=False)[0]).with_nms(
                threshold=0.1)

            if len(ball_dets) > 0:
                best = ball_dets[np.argmax(ball_dets.confidence):np.argmax(ball_dets.confidence) + 1]
                results['ball'] = self.ball_tracker.update_with_detections(best)

        for tracker_id in list(self.last_seen_players.keys()):

            if results['players'] is None or tracker_id not in results['players'].tracker_id:
                self.last_seen_players[tracker_id]['frame'] += 1

                if self.last_seen_players[tracker_id]['frame'] > self.max_missing_frames:
                    del self.last_seen_players[tracker_id]

            else:
                self.last_seen_players[tracker_id]['frame'] = 0  # Yeniden görüldü

        return results

    def annotate_original_frame(self, frame: np.ndarray, detections: Dict[str, Optional[sv.Detections]],
                                annotator: FrameAnnotator, show_jersey_analysis: bool = True) -> np.ndarray:
        team_centroids = {0: self.team0_centroid, 1: self.team1_centroid} if show_jersey_analysis else None
        annotated = annotator.annotate_frame(
            frame,
            detections,
            team_assignments=self.player_team_assignments if show_jersey_analysis else None,
            team_centroids=team_centroids,
            show_jersey_regions=show_jersey_analysis
        )

        return annotated

    def create_radar_image(self, detections: Dict[str, Optional[sv.Detections]], transformer: ViewTransformer,
                           include_paths: bool = True) -> np.ndarray:
        radar_image = draw_pitch(config=self.pitch_config)
        team_colors = {}
        team_colors[0] = sv.Color(r=int(self.team0_centroid[0]), g=int(self.team0_centroid[1]),
                                  b=int(self.team0_centroid[2])) if self.team0_centroid is not None else sv.Color.BLUE
        team_colors[1] = sv.Color(r=int(self.team1_centroid[0]), g=int(self.team1_centroid[1]),
                                  b=int(self.team1_centroid[2])) if self.team1_centroid is not None else sv.Color.RED
        color_map = {'goalkeepers': sv.Color.GREEN, 'referees': sv.Color.YELLOW, 'ball': sv.Color.RED}
        player_dets = detections.get('players')

        if player_dets is not None and player_dets.tracker_id is not None:

            coords, coords_pitch = player_dets.get_anchors_coordinates(
                sv.Position.BOTTOM_CENTER), transformer.transform_points(
                player_dets.get_anchors_coordinates(sv.Position.BOTTOM_CENTER))

            for i, tracker_id in enumerate(player_dets.tracker_id):

                team_id, color, point = self.player_team_assignments.get(tracker_id, -1), team_colors.get(
                    self.player_team_assignments.get(tracker_id, -1), sv.Color.WHITE), coords_pitch[i]

                if 0 <= point[0] <= self.pitch_config.length and 0 <= point[1] <= self.pitch_config.width:
                    radar_image = draw_points_on_pitch(config=self.pitch_config, xy=np.array([point]), face_color=color,
                                                       edge_color=sv.Color.BLACK, radius=8, pitch=radar_image)

        for key in ['goalkeepers', 'referees', 'ball']:
            dets = detections.get(key)

            if dets is None or len(dets) == 0 or dets.tracker_id is None: continue

            coords, coords_pitch = dets.get_anchors_coordinates(
                sv.Position.CENTER if key == 'ball' else sv.Position.BOTTOM_CENTER), transformer.transform_points(
                dets.get_anchors_coordinates(sv.Position.CENTER if key == 'ball' else sv.Position.BOTTOM_CENTER))

            for point in coords_pitch:

                if 0 <= point[0] <= self.pitch_config.length and 0 <= point[1] <= self.pitch_config.width:
                    radar_image = draw_points_on_pitch(config=self.pitch_config, xy=np.array([point]),
                                                       face_color=color_map[key], edge_color=sv.Color.BLACK,
                                                       radius=10 if key == 'ball' else 8, pitch=radar_image)

        if include_paths:
            for tracker_id, history in self.movement_history.items():
                if len(history) >= 2:
                    try:
                        id_int = int(str(tracker_id).split('_')[-1])
                    except Exception:
                        id_int = tracker_id
                    team_id = self.player_team_assignments.get(id_int, -1)
                    color = team_colors.get(team_id, sv.Color.WHITE)

                    try:
                        radar_image = draw_paths_on_pitch(config=self.pitch_config, paths=[np.array(history)],
                                                          colors=[color], pitch=radar_image)

                    except Exception:
                        radar_image = draw_paths_on_pitch(config=self.pitch_config, paths=[np.array(history)], colors=[
                            color.as_bgr() if hasattr(color, 'as_bgr') else (255, 255, 255)], pitch=radar_image)

        return radar_image

    def track_player_movement(self, detections: Dict[str, Optional[sv.Detections]],
                              transformer: ViewTransformer) -> None:

        for key in ['players', 'goalkeepers', 'ball']:
            dets = detections.get(key)

            if dets is None or dets.tracker_id is None: continue
            coords, coords_pitch = dets.get_anchors_coordinates(
                sv.Position.CENTER if key == 'ball' else sv.Position.BOTTOM_CENTER), transformer.transform_points(
                dets.get_anchors_coordinates(sv.Position.CENTER if key == 'ball' else sv.Position.BOTTOM_CENTER))

            for i, tracker_id in enumerate(dets.tracker_id):

                unique_id = f"{key}_{tracker_id}"

                if unique_id not in self.movement_history: self.movement_history[unique_id] = []

                self.movement_history[unique_id].append(tuple(coords_pitch[i]))

                if len(self.movement_history[unique_id]) > self.path_history_length:
                    self.movement_history[unique_id] = self.movement_history[unique_id][-self.path_history_length:]

    def _extract_jersey_region(self, frame: np.ndarray, bbox: np.ndarray) -> np.ndarray:
        x1, y1, x2, y2 = bbox.astype(int)
        width, height = x2 - x1, y2 - y1
        jersey_x1, jersey_x2 = x1 + int(width * 0.35), x1 + int(width * 0.65)
        jersey_y1, jersey_y2 = y1 + int(height * 0.3), y1 + int(height * 0.55)
        jersey_y1, jersey_y2 = np.clip(jersey_y1, 0, frame.shape[0] - 1), np.clip(jersey_y2, 0, frame.shape[0] - 1)
        jersey_x1, jersey_x2 = np.clip(jersey_x1, 0, frame.shape[1] - 1), np.clip(jersey_x2, 0, frame.shape[1] - 1)
        
        if jersey_y2 <= jersey_y1 or jersey_x2 <= jersey_x1: return np.array([])

        jersey_roi = frame[jersey_y1:jersey_y2, jersey_x1:jersey_x2]
        jersey_roi = cv2.medianBlur(jersey_roi, 3)

        return cv2.cvtColor(jersey_roi, cv2.COLOR_BGR2RGB)

    def _compute_dominant_color(self, region: np.ndarray, num_clusters: int = 3) -> Optional[np.ndarray]:

        if region.size == 0 or region.shape[0] * region.shape[1] < num_clusters: return None
        
        hsv_pixels = cv2.cvtColor(region, cv2.COLOR_RGB2HSV).reshape(-1, 3).astype(np.float32)
        kmeans = KMeans(n_clusters=num_clusters, n_init=10, random_state=0)
        kmeans.fit(hsv_pixels)
        dominant_cluster_idx = np.argmax(np.bincount(kmeans.labels_))
        dominant_color_hsv = kmeans.cluster_centers_[dominant_cluster_idx]

        return cv2.cvtColor(np.uint8([[dominant_color_hsv]]), cv2.COLOR_HSV2RGB)[0][0]

    def classify_teams_by_jersey_color(self, detections: Dict[str, Optional[sv.Detections]], frame: np.ndarray) -> Dict[
        int, int]:

        dets = detections.get('players')

        if dets is None or dets.tracker_id is None or len(dets) == 0: return {}

        dominant_colors, tracker_ids = [], []

        for i in range(len(dets)):

            bbox, tracker_id = dets.xyxy[i], dets.tracker_id[i]
            jersey = self._extract_jersey_region(frame, bbox)
            color = self._compute_dominant_color(jersey)

            if color is not None:
                dominant_colors.append(color)
                tracker_ids.append(tracker_id)

        if len(dominant_colors) < 2: return {}

        kmeans = KMeans(n_clusters=2, n_init=10, random_state=0).fit(dominant_colors)
        self.team0_centroid, self.team1_centroid = kmeans.cluster_centers_

        return {tracker_ids[i]: kmeans.labels_[i] for i in range(len(tracker_ids))}

    def update_team_classification(self, detections: Dict[str, Optional[sv.Detections]], frame: np.ndarray) -> None:
        current_assignments = self.classify_teams_by_jersey_color(detections, frame)

        if current_assignments: self.player_team_assignments.update(current_assignments)


class VideoProcessor:

    def __init__(self, video_path: str, output_path: str, frame_processor: FrameProcessor,
                 frame_annotator: FrameAnnotator, radar_width: int = 1600, radar_height: int = 1000):
        self.video_path = video_path
        self.output_path = output_path
        self.radar_width = radar_width
        self.radar_height = radar_height
        self.frame_processor = frame_processor
        self.frame_annotator = frame_annotator
        self.cap = None
        self.total_frames = 0
        self.last_radar = np.zeros((self.radar_height, self.radar_width, 3), dtype=np.uint8)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    def setup_video_io(self) -> bool:

        self.cap = cv2.VideoCapture(self.video_path)

        if not self.cap.isOpened():
            print("Error: Could not open video file.")

            return False

        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 25
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        return True

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        # Parallel tasks için future objects
        keypoints_future = self.executor.submit(self.frame_processor.detect_keypoints, frame)
        detections_future = self.executor.submit(self.frame_processor.detect_objects, frame)
        # Keypoints ve detections'ı parallel olarak al
        transformer = keypoints_future.result()
        detections = detections_future.result()
        # Team sınıflandırması
        team_future = self.executor.submit(
            self.frame_processor.update_team_classification,
            detections,
            frame
        )

        # Annotation işlemini parallel yap

        annotation_future = self.executor.submit(
            self.frame_processor.annotate_original_frame,
            frame.copy(),
            detections,
            self.frame_annotator
        )

        # Team sınıflandırması bitene kadar bekle
        team_future.result()
        # Annotated frame'i al
        annotated = annotation_future.result()
        # Radar oluşturma
        if transformer:

            radar_future = self.executor.submit(
                self._create_radar_with_tracking,
                detections,
                transformer
            )

            radar = radar_future.result()

        else:
            radar = self._handle_missing_transformer()

        return annotated, radar

    def _create_radar_with_tracking(self, detections, transformer) -> np.ndarray:
            """Radar oluşturma ve tracking işlemlerini handle eden yardımcı method"""
            # Hareket geçmişi hala toplanır, bu satır kalabilir veya kaldırılabilir.
            self.frame_processor.track_player_movement(detections, transformer)
            
            # Fonksiyonu include_paths=False parametresiyle çağırarak yolların çizilmesini engelleyin.
            radar = self.frame_processor.create_radar_image(detections, transformer, include_paths=False) # <--- DEĞİŞİKLİK BURADA
            
            radar = cv2.resize(radar, (self.radar_width, self.radar_height))
            self.last_radar = radar.copy()
            return radar

    def _handle_missing_transformer(self) -> np.ndarray:
        """Transformer olmadığında radar handling"""
        radar = self.last_radar.copy()
        cv2.putText(
            radar,
            "No Keypoints Detected",
            (50, self.radar_height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        return radar

    def __del__(self):
        """Cleanup için executor'ı kapat"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


def check_cuda():
    # CUDA kullanılabilir mi kontrol et
    cuda_available = torch.cuda.is_available()
    print(f"CUDA kullanılabilir mi?: {cuda_available}")
    if cuda_available:
        # Mevcut CUDA cihazı sayısını göster
        device_count = torch.cuda.device_count()
        print(f"Kullanılabilir CUDA cihazı sayısı: {device_count}")
        # Aktif CUDA cihazının ismini göster
        current_device = torch.cuda.current_device()
        device_name = torch.cuda.get_device_name(current_device)
        print(f"Kullanılan CUDA cihazı: {device_name}")
        # Mevcut cihazı göster
        device = torch.device("cuda")
        print(f"Aktif cihaz: {device}")

    else:
        print("CUDA kullanılamıyor, CPU kullanılacak")
        device = torch.device("cpu")
        print(f"Aktif cihaz: {device}")