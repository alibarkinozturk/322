from typing import Tuple, Optional
import cv2
import numpy as np
import numpy.typing as npt


class ViewTransformer:


    def __init__(
            self,
            source: npt.NDArray[np.float32],
            target: npt.NDArray[np.float32]
    ) -> None:

        # Giriş verilerinin doğruluğunu kontrol et
        if source.shape != target.shape:
            raise ValueError("Source and target must have the same shape.")
        if source.shape[1] != 2:
            raise ValueError("Source and target points must be 2D coordinates.")

        # Veri tiplerini numpy.float32'ye dönüştür
        source = source.astype(np.float32)
        target = target.astype(np.float32)

        # Homografi matrisini hesapla
        self.m: Optional[npt.NDArray[np.float32]] = None
        if len(source) < 3:
            raise ValueError("At least 4 points are required to compute a homography")
        else:
            # Homografi matrisini hesapla ve sınıf değişkenine kaydet
            self.m, _ = cv2.findHomography(source, target)

    def transform_points(
            self,
            points: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:

        # Boş girişler için erken dönüş
        if points.size == 0:
            return np.array([], dtype=np.float32).reshape(0, 2)

        # Homografi matrisinin var olup olmadığını kontrol et
        if self.m is None:
            raise RuntimeError("Homography matrix is not computed. Initialize with valid points.")

        # Girdi verilerinin doğruluğunu kontrol et
        if points.shape[1] != 2:
            raise ValueError("Points must be 2D coordinates.")

        # Perspektif dönüşüm için noktaları yeniden şekillendir
        reshaped_points = points.reshape(-1, 1, 2).astype(np.float32)
        # Perspektif dönüşüm uygula
        transformed_points = cv2.perspectiveTransform(reshaped_points, self.m)
        # Orijinal şekle geri dönüştür
        return transformed_points.reshape(-1, 2)

    def transform_image(
            self,
            image: npt.NDArray[np.uint8],
            resolution_wh: Tuple[int, int]
    ) -> npt.NDArray[np.uint8]:

        # Homografi matrisinin var olup olmadığını kontrol et
        if self.m is None:
            raise RuntimeError("Homography matrix is not computed. Initialize with valid points.")

        # Görüntü boyutlarını kontrol et
        if len(image.shape) not in {2, 3}:
            raise ValueError("Image must be either grayscale or color.")

        # Perspektif dönüşüm uygula
        return cv2.warpPerspective(image, self.m, resolution_wh)