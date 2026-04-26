from dataclasses import dataclass
import logging
import os
import socket
import time
import urllib.error
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


INSIGHTFACE_MODEL_NAME = "insightface-buffalo_sc-v1"
INSIGHTFACE_PACK_NAME = "buffalo_sc"
INSIGHTFACE_MODEL_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "insightface",
)

MEDIAPIPE_MODEL_NAME = "mediapipe-face-landmarker-v1"
FACE_LANDMARKER_TASK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "face_landmarker.task",
)
FACE_LANDMARKER_TASK_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)


def download_with_retry(url, dest, retries=3, timeout=30):
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                with open(dest, "wb") as f:
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
            return
        except (urllib.error.URLError, socket.timeout, OSError) as exc:
            logging.warning("Download attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            if attempt < retries:
                time.sleep(2)
    raise RuntimeError(f"Failed to download {url} after {retries} attempts.")


@dataclass
class FaceEmbeddingResult:
    model_name: str
    embedding: list[float]


def create_embedder(backend="insightface"):
    if backend == "insightface":
        return InsightFaceEmbedder()
    if backend == "mediapipe":
        return MediaPipeFaceEmbedder()
    raise ValueError(f"Unknown embedding backend '{backend}'")


class InsightFaceEmbedder:
    """
    Uses InsightFace's recognition embedding as the primary identity representation.
    """

    def __init__(self, model_pack=INSIGHTFACE_PACK_NAME, det_size=(640, 640)):
        try:
            from insightface.app import FaceAnalysis
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "InsightFace is not installed. Install it with "
                "'.venv/bin/pip install insightface onnxruntime'."
            ) from exc

        os.makedirs(INSIGHTFACE_MODEL_ROOT, exist_ok=True)

        self._app = FaceAnalysis(
            name=model_pack,
            root=INSIGHTFACE_MODEL_ROOT,
            providers=["CPUExecutionProvider"],
        )
        self._app.prepare(ctx_id=-1, det_size=det_size)

    def close(self):
        return None

    def embed_image_file(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not read image at '{image_path}'")

        return self.embed_bgr_image(image)

    def embed_bgr_image(self, image):
        faces = self._app.get(image)
        if not faces:
            raise ValueError("No face detected in the provided image.")

        best_face = max(faces, key=lambda face: (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1]))
        embedding = best_face.normed_embedding.tolist()
        return FaceEmbeddingResult(model_name=INSIGHTFACE_MODEL_NAME, embedding=embedding)


class MediaPipeFaceEmbedder:
    """
    Fallback baseline using MediaPipe face landmarks when InsightFace is unavailable.
    """

    def __init__(self, max_num_faces=1):
        if not os.path.exists(FACE_LANDMARKER_TASK_PATH):
            logging.info("Downloading MediaPipe face landmarker model (one-time)...")
            download_with_retry(FACE_LANDMARKER_TASK_URL, FACE_LANDMARKER_TASK_PATH)

        base_options = python.BaseOptions(model_asset_path=FACE_LANDMARKER_TASK_PATH)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=max_num_faces,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def close(self):
        self._landmarker.close()

    def embed_image_file(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not read image at '{image_path}'")

        return self.embed_bgr_image(image)

    def embed_bgr_image(self, image):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)

        if not result.face_landmarks:
            raise ValueError("No face detected in the provided image.")

        embedding = self._normalize_landmarks(result.face_landmarks[0])
        return FaceEmbeddingResult(model_name=MEDIAPIPE_MODEL_NAME, embedding=embedding)

    def _normalize_landmarks(self, landmarks):
        coordinates = [(landmark.x, landmark.y, landmark.z) for landmark in landmarks]

        centroid_x = sum(point[0] for point in coordinates) / len(coordinates)
        centroid_y = sum(point[1] for point in coordinates) / len(coordinates)
        centroid_z = sum(point[2] for point in coordinates) / len(coordinates)

        normalized_points = []
        squared_sum = 0.0
        for x_value, y_value, z_value in coordinates:
            nx = x_value - centroid_x
            ny = y_value - centroid_y
            nz = z_value - centroid_z
            normalized_points.append((nx, ny, nz))
            squared_sum += nx * nx + ny * ny + nz * nz

        scale = squared_sum ** 0.5
        if scale == 0:
            raise ValueError("Detected face landmarks could not be normalized.")

        flattened = []
        for nx, ny, nz in normalized_points:
            flattened.extend([nx / scale, ny / scale, nz / scale])

        return flattened
