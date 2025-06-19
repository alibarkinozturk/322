from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SoccerPitchConfiguration:

    width: int = 6800  # Saha genişliği [cm]
    length: int = 10500  # Saha uzunluğu [cm]
    penalty_box_width: int = 4032  # Ceza sahası genişliği [cm]
    penalty_box_length: int = 1650  # Ceza sahası uzunluğu [cm]
    goal_box_width: int = 1832  # Kale sahası genişliği [cm]
    goal_box_length: int = 550  # Kale sahası uzunluğu [cm]
    centre_circle_radius: int = 915  # Orta saha çember yarıçapı [cm]
    penalty_spot_distance: int = 1100  # Penaltı noktası mesafesi [cm]
    penalty_arc_radius: int = 915
    @property
    def vertices(self) -> List[Tuple[int, int]]:

        half_width = self.width / 2
        half_length = self.length / 2
        half_penalty_box_width = self.penalty_box_width / 2
        half_goal_box_width = self.goal_box_width / 2

        return [
            (0, 0),  # 1 - Sol alt köşe
            (0, (self.width - self.penalty_box_width) / 2),  # 2 - Sol ceza sahası alt köşesi
            (0, (self.width - self.goal_box_width) / 2),  # 3 - Sol kale sahası alt köşesi
            (0, (self.width + self.goal_box_width) / 2),  # 4 - Sol kale sahası üst köşesi
            (0, (self.width + self.penalty_box_width) / 2),  # 5 - Sol ceza sahası üst köşesi
            (0, self.width),  # 6 - Sol üst köşe
            (self.goal_box_length, (self.width - self.goal_box_width) / 2),  # 7 - Sol kale sahası iç alt köşesi
            (self.goal_box_length, (self.width + self.goal_box_width) / 2),  # 8 - Sol kale sahası iç üst köşesi
            (self.penalty_spot_distance, half_width),  # 9 - Sol penaltı noktası
            (self.penalty_box_length, (self.width - self.penalty_box_width) / 2),  # 10 - Sol ceza sahası iç alt köşesi
            (self.penalty_box_length, (self.width - self.goal_box_width) / 2),  # 11
            (self.penalty_box_length, (self.width + self.goal_box_width) / 2),  # 12
            (self.penalty_box_length, (self.width + self.penalty_box_width) / 2),  # 13 - Sol ceza sahası iç üst köşesi
            (half_length, 0),  # 14 - Orta alt nokta
            (half_length, half_width - self.centre_circle_radius),  # 15 - Orta çember alt noktası
            (half_length, half_width + self.centre_circle_radius),  # 16 - Orta çember üst noktası
            (half_length, self.width),  # 17 - Orta üst nokta
            (self.length - self.penalty_box_length, (self.width - self.penalty_box_width) / 2),
            # 18 - Sağ ceza sahası iç alt köşesi
            (self.length - self.penalty_box_length, (self.width - self.goal_box_width) / 2),  # 19
            (self.length - self.penalty_box_length, (self.width + self.goal_box_width) / 2),  # 20
            (self.length - self.penalty_box_length, (self.width + self.penalty_box_width) / 2),
            # 21 - Sağ ceza sahası iç üst köşesi
            (self.length - self.penalty_spot_distance, half_width),  # 22 - Sağ penaltı noktası
            (self.length - self.goal_box_length, (self.width - self.goal_box_width) / 2),
            # 23 - Sağ kale sahası iç alt köşesi
            (self.length - self.goal_box_length, (self.width + self.goal_box_width) / 2),
            # 24 - Sağ kale sahası iç üst köşesi
            (self.length, 0),  # 25 - Sağ alt köşe
            (self.length, (self.width - self.penalty_box_width) / 2),  # 26 - Sağ ceza sahası alt köşesi
            (self.length, (self.width - self.goal_box_width) / 2),  # 27 - Sağ kale sahası alt köşesi
            (self.length, (self.width + self.goal_box_width) / 2),  # 28 - Sağ kale sahası üst köşesi
            (self.length, (self.width + self.penalty_box_width) / 2),  # 29 - Sağ ceza sahası üst köşesi
            (self.length, self.width),  # 30 - Sağ üst köşe
            (half_length - self.centre_circle_radius, half_width),  # 31 - Orta çember sol noktası
            (half_length + self.centre_circle_radius, half_width),  # 32 - Orta çember sağ noktası
        ]

    # Saha çizgilerini tanımlayan kenar listesi (1-indexed)
    edges: List[Tuple[int, int]] = field(default_factory=lambda: [
        (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),  # Sol kenar çizgileri
        (7, 8),  # Sol kale sahası çizgisi
        (10, 11), (11, 12), (12, 13),  # Sol ceza sahası çizgisi
        (14, 15), (15, 16), (16, 17),  # Orta çizgi
        (18, 19), (19, 20), (20, 21),  # Sağ ceza sahası çizgisi
        (23, 24),  # Sağ kale sahası çizgisi
        (25, 26), (26, 27), (27, 28), (28, 29), (29, 30),  # Sağ kenar çizgileri
        (1, 14), (2, 10), (3, 7), (4, 8), (5, 13), (6, 17),  # Sol yarı saha yatay çizgileri
        (14, 25), (18, 26), (23, 27), (24, 28), (21, 29), (17, 30)  # Sağ yarı saha yatay çizgileri
    ])

    # Nokta etiketleri
    labels: List[str] = field(default_factory=lambda: [
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "13", "15", "16", "17", "18", "20", "21", "22",
        "23", "24", "25", "26", "27", "28", "29", "30", "31", "32",
        "14", "19"
    ])

    # Nokta renkleri (Pembe: Sol yarı saha, Mavi: Orta çizgi, Turuncu: Sağ yarı saha)
    colors: List[str] = field(default_factory=lambda: [
        "#FF1493", "#FF1493", "#FF1493", "#FF1493", "#FF1493", "#FF1493",
        "#FF1493", "#FF1493", "#FF1493", "#FF1493", "#FF1493", "#FF1493",
        "#FF1493", "#00BFFF", "#00BFFF", "#00BFFF", "#00BFFF", "#FF6347",
        "#FF6347", "#FF6347", "#FF6347", "#FF6347", "#FF6347", "#FF6347",
        "#FF6347", "#FF6347", "#FF6347", "#FF6347", "#FF6347", "#FF6347",
        "#00BFFF", "#00BFFF"
    ])