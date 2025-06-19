import numpy as np
from typing import Optional, List, Tuple
import cv2
import supervision as sv


def draw_pitch(
        config: 'SoccerPitchConfiguration',
        background_color: sv.Color = sv.Color(34, 139, 34),  # Yeşil
        line_color: sv.Color = sv.Color.WHITE,
        padding: int = 50,
        line_thickness: int = 2,
        point_radius: int = 4,
        scale: float = 0.1,
        width: int = 1152,
        height: int = 756
) -> np.ndarray:

    # Belirtilen boyut ve renkte saha arkaplanı oluştur
    pitch = np.ones((height, width, 3), dtype=np.uint8) * np.array(background_color.as_bgr(), dtype=np.uint8)

    # Saha çizgilerini çiz
    for edge in config.edges:
        # 1-indexed olduğu için -1 yaparak 0-indexed'e dönüştür
        start_idx, end_idx = edge
        start = config.vertices[start_idx - 1]
        end = config.vertices[end_idx - 1]

        # Koordinatları ölçekle ve padding ekle
        start_x, start_y = int(start[0] * scale) + padding, int(start[1] * scale) + padding
        end_x, end_y = int(end[0] * scale) + padding, int(end[1] * scale) + padding

        # Çizgiyi çiz
        cv2.line(
            img=pitch,
            pt1=(start_x, start_y),
            pt2=(end_x, end_y),
            color=line_color.as_bgr(),
            thickness=line_thickness
        )

    # Orta saha dairesini çiz
    center_circle_center = (
        int(config.length * scale / 2) + padding,
        int(config.width * scale / 2) + padding
    )
    cv2.circle(
        img=pitch,
        center=center_circle_center,
        radius=int(config.centre_circle_radius * scale),
        color=line_color.as_bgr(),
        thickness=line_thickness
    )

    # Penaltı noktalarını çiz
    penalty_spots = [
        (int(config.penalty_spot_distance * scale) + padding,
         int(config.width * scale / 2) + padding),
        (int(config.length * scale) - int(config.penalty_spot_distance * scale) + padding,
         int(config.width * scale / 2) + padding)
    ]

    # Ceza sahası yaylarını çiz
    # Sol ceza sahası yayı
    left_penalty_arc_center = (
        int(config.penalty_spot_distance * scale) + padding,
        int(config.width * scale / 2) + padding
    )

    # Yayın başlangıç ve bitiş açıları (penaltı noktasından bakıldığında ceza sahasının dışında kalan yay)
    # Açılar derece cinsinden ve saat yönünün tersine
    draw_penalty_arc(
        pitch=pitch,
        center=left_penalty_arc_center,
        radius=int(config.penalty_arc_radius * scale),
        start_angle=-50,  # Yaklaşık başlangıç açısı
        end_angle=50,  # Yaklaşık bitiş açısı
        color=line_color.as_bgr(),
        thickness=line_thickness
    )

    # Sağ ceza sahası yayı
    right_penalty_arc_center = (
        int(config.length * scale) - int(config.penalty_spot_distance * scale) + padding,
        int(config.width * scale / 2) + padding
    )
    draw_penalty_arc(
        pitch=pitch,
        center=right_penalty_arc_center,
        radius=int(config.penalty_arc_radius * scale),
        start_angle=130,  # Yaklaşık başlangıç açısı
        end_angle=230,  # Yaklaşık bitiş açısı
        color=line_color.as_bgr(),
        thickness=line_thickness
    )

    for spot in penalty_spots:
        cv2.circle(
            img=pitch,
            center=spot,
            radius=point_radius,
            color=line_color.as_bgr(),
            thickness=-1  # İçi dolu daire
        )

    return pitch

def draw_penalty_arc(
        pitch: np.ndarray,
        center: Tuple[int, int],
        radius: int,
        start_angle: int,
        end_angle: int,
        color: Tuple[int, int, int],
        thickness: int = 2
) -> None:

    # OpenCV'de açılar derece cinsinden ve saat yönünde
    cv2.ellipse(
        img=pitch,
        center=center,
        axes=(radius, radius),  # Dairesel yay için x ve y eksenleri aynı
        angle=0,  # Döndürme açısı
        startAngle=start_angle,
        endAngle=end_angle,
        color=color,
        thickness=thickness
    )
def draw_points_on_pitch(
        config: 'SoccerPitchConfiguration',
        xy: np.ndarray,
        face_color: sv.Color = sv.Color.RED,
        edge_color: sv.Color = sv.Color.BLACK,
        radius: int = 10,
        thickness: int = 2,
        padding: int = 50,
        scale: float = 0.1,
        pitch: Optional[np.ndarray] = None
) -> np.ndarray:

    # Eğer saha görüntüsü verilmemişse yeni bir tane oluştur
    if pitch is None:
        pitch = draw_pitch(
            config=config,
            padding=padding,
            scale=scale
        )

    # Her bir noktayı çiz
    for point in xy:
        # Koordinatları ölçekle ve padding ekle
        scaled_x = int(point[0] * scale) + padding
        scaled_y = int(point[1] * scale) + padding

        # İçi dolu daire çiz
        cv2.circle(
            img=pitch,
            center=(scaled_x, scaled_y),
            radius=radius,
            color=face_color.as_bgr(),
            thickness=-1  # İçi dolu daire
        )

        # Daire kenarını çiz
        cv2.circle(
            img=pitch,
            center=(scaled_x, scaled_y),
            radius=radius,
            color=edge_color.as_bgr(),
            thickness=thickness
        )

    return pitch


def draw_paths_on_pitch(
        config: 'SoccerPitchConfiguration',
        paths: List[np.ndarray],
        colors: Optional[List[sv.Color]] = None,
        thickness: int = 2,
        padding: int = 50,
        scale: float = 0.1,
        pitch: Optional[np.ndarray] = None
) -> np.ndarray:

    # Eğer saha görüntüsü verilmemişse yeni bir tane oluştur
    if pitch is None:
        pitch = draw_pitch(
            config=config,
            padding=padding,
            scale=scale
        )

    # Eğer renk listesi verilmemişse, varsayılan olarak beyaz kullan
    if colors is None:
        colors = [sv.Color.WHITE] * len(paths)
    # Eğer renk sayısı yol sayısından az ise, renkleri döngü ile tekrarla
    elif len(colors) < len(paths):
        colors = colors * (len(paths) // len(colors) + 1)
        colors = colors[:len(paths)]

    # Her bir yolu çiz
    for i, path in enumerate(paths):
        # Boş yolları atla
        if path.size == 0 or len(path) < 2:
            continue

        # Koordinatları ölçekle ve padding ekle
        scaled_path = []
        for point in path:
            scaled_x = int(point[0] * scale) + padding
            scaled_y = int(point[1] * scale) + padding
            scaled_path.append((scaled_x, scaled_y))

        # Ardışık noktaları çizgilerle birleştir
        for j in range(len(scaled_path) - 1):
            cv2.line(
                img=pitch,
                pt1=scaled_path[j],
                pt2=scaled_path[j + 1],
                color=colors[i].as_bgr(),
                thickness=thickness
            )

    return pitch