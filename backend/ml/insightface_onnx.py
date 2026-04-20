"""
InsightFace ONNX inference — no insightface pip package required.
Uses buffalo_l model files directly via onnxruntime.

Models (in <repo_root>/buffalo_l/):
  det_10g.onnx  — SCRFD face detector (outputs 5-point keypoints)
  w600k_r50.onnx — ArcFace R50 recognition (512-d embedding)
"""
import cv2
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# buffalo_l lives two levels above backend/ml/
_BUFFALO_DIR = Path(__file__).resolve().parent.parent.parent / "buffalo_l"
DET_MODEL_PATH = _BUFFALO_DIR / "det_10g.onnx"
REC_MODEL_PATH = _BUFFALO_DIR / "w600k_r50.onnx"

# Detection input size (fixed for det_10g.onnx)
_DET_SIZE = (640, 640)
_STRIDES = [8, 16, 32]
_NUM_ANCHORS = 2

# Standard 5-point face template for 112x112 alignment (InsightFace convention)
_FACE_TEMPLATE = np.array([
    [38.2946, 51.6963],  # left eye
    [73.5318, 51.5014],  # right eye
    [56.0252, 71.7366],  # nose tip
    [41.5493, 92.3655],  # left mouth corner
    [70.7299, 92.2041],  # right mouth corner
], dtype=np.float32)

_det_session = None
_rec_session = None


# ---------------------------------------------------------------------------
# Session loaders
# ---------------------------------------------------------------------------

def _get_det():
    global _det_session
    if _det_session is None:
        import onnxruntime as ort
        if not DET_MODEL_PATH.exists():
            raise FileNotFoundError(f"Detection model not found: {DET_MODEL_PATH}")
        _det_session = ort.InferenceSession(
            str(DET_MODEL_PATH), providers=["CPUExecutionProvider"]
        )
    return _det_session


def _get_rec():
    global _rec_session
    if _rec_session is None:
        import onnxruntime as ort
        if not REC_MODEL_PATH.exists():
            raise FileNotFoundError(f"Recognition model not found: {REC_MODEL_PATH}")
        _rec_session = ort.InferenceSession(
            str(REC_MODEL_PATH), providers=["CPUExecutionProvider"]
        )
    return _rec_session


# ---------------------------------------------------------------------------
# SCRFD detection helpers
# ---------------------------------------------------------------------------

def _preprocess_det(image: np.ndarray) -> np.ndarray:
    """Resize + normalize image for SCRFD."""
    resized = cv2.resize(image, _DET_SIZE)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32)
    rgb = (rgb - 127.5) / 128.0
    return np.transpose(rgb, (2, 0, 1))[np.newaxis, :]  # NCHW


def _anchor_centers(stride: int) -> np.ndarray:
    """Generate anchor center coordinates (x, y) for a given stride on a 640×640 input."""
    fh = _DET_SIZE[1] // stride
    fw = _DET_SIZE[0] // stride
    # Each grid cell has _NUM_ANCHORS anchors
    j = np.tile(np.arange(fw, dtype=np.float32), fh * _NUM_ANCHORS)
    i = np.repeat(np.repeat(np.arange(fh, dtype=np.float32), fw), _NUM_ANCHORS)
    j = j.reshape(-1, _NUM_ANCHORS).flatten()  # repeat anchor dim
    i = np.repeat(np.arange(fh, dtype=np.float32), fw * _NUM_ANCHORS)

    # Rebuild properly: (fh, fw, num_anchors) → flatten
    centers = []
    for ri in range(fh):
        for ci in range(fw):
            for _ in range(_NUM_ANCHORS):
                centers.append([ci * stride, ri * stride])
    return np.array(centers, dtype=np.float32)


def _decode_boxes(centers: np.ndarray, dist: np.ndarray, stride: int) -> np.ndarray:
    """Distance-to-bbox decoding (SCRFD uses FCOS-style distances)."""
    d = dist * stride
    x1 = centers[:, 0] - d[:, 0]
    y1 = centers[:, 1] - d[:, 1]
    x2 = centers[:, 0] + d[:, 2]
    y2 = centers[:, 1] + d[:, 3]
    return np.stack([x1, y1, x2, y2], axis=1)


def _decode_kps(centers: np.ndarray, kps_pred: np.ndarray, stride: int) -> np.ndarray:
    """Decode 5-point keypoints from SCRFD predictions."""
    kp = kps_pred * stride
    kps_x = centers[:, 0:1] + kp[:, 0::2]  # (N, 5)
    kps_y = centers[:, 1:2] + kp[:, 1::2]  # (N, 5)
    return np.stack([kps_x, kps_y], axis=2)  # (N, 5, 2)


def _nms(boxes: np.ndarray, scores: np.ndarray, iou_thr: float = 0.4) -> list:
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        iou = (w * h) / (areas[i] + areas[order[1:]] - w * h)
        order = order[1:][iou <= iou_thr]
    return keep


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_faces(image: np.ndarray, score_thr: float = 0.5) -> list:
    """
    Detect all faces in image using SCRFD (det_10g.onnx).

    Returns list of dicts:
        { "bbox": [x1, y1, x2, y2],  "kps": ndarray(5, 2),  "score": float }
    Results are in original image coordinates, sorted by score descending.
    """
    h, w = image.shape[:2]
    blob = _preprocess_det(image)

    outputs = _get_det().run(None, {"input.1": blob})
    # Outputs: [scores_8, scores_16, scores_32, boxes_8, boxes_16, boxes_32,
    #            kps_8,    kps_16,    kps_32]

    sx = w / _DET_SIZE[0]
    sy = h / _DET_SIZE[1]

    all_boxes, all_scores, all_kps = [], [], []

    for n, stride in enumerate(_STRIDES):
        scores = outputs[n][:, 0]
        box_dist = outputs[n + 3]
        kps_dist = outputs[n + 6]

        mask = scores >= score_thr
        if not mask.any():
            continue

        centers = _anchor_centers(stride)
        boxes = _decode_boxes(centers[mask], box_dist[mask], stride)
        kps = _decode_kps(centers[mask], kps_dist[mask], stride)

        # Scale to original image size
        boxes[:, [0, 2]] *= sx
        boxes[:, [1, 3]] *= sy
        kps[:, :, 0] *= sx
        kps[:, :, 1] *= sy

        all_boxes.append(boxes)
        all_scores.append(scores[mask])
        all_kps.append(kps)

    if not all_boxes:
        return []

    all_boxes = np.concatenate(all_boxes)
    all_scores = np.concatenate(all_scores)
    all_kps = np.concatenate(all_kps)

    keep = _nms(all_boxes, all_scores)

    results = []
    for i in keep:
        results.append({
            "bbox": all_boxes[i].tolist(),
            "kps": all_kps[i],
            "score": float(all_scores[i]),
        })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def align_face(image: np.ndarray, kps: np.ndarray) -> np.ndarray:
    """
    Align a detected face to 112×112 using 5-point keypoints.
    kps: ndarray of shape (5, 2) in (x, y) order.
    """
    M, _ = cv2.estimateAffinePartial2D(kps, _FACE_TEMPLATE, method=cv2.LMEDS)
    if M is None:
        raise ValueError("Could not compute affine transform for face alignment.")
    return cv2.warpAffine(image, M, (112, 112), borderValue=0)


def get_embedding(face_112: np.ndarray) -> list:
    """
    Extract a 512-d L2-normalised ArcFace embedding from a 112×112 BGR face crop.
    Returns a plain list of floats.
    """
    rgb = cv2.cvtColor(face_112, cv2.COLOR_BGR2RGB).astype(np.float32)
    rgb = (rgb - 127.5) / 128.0
    blob = np.transpose(rgb, (2, 0, 1))[np.newaxis, :]  # (1, 3, 112, 112)
    output = _get_rec().run(None, {"input.1": blob})[0][0]  # (512,)
    norm = np.linalg.norm(output)
    if norm == 0:
        raise ValueError("Zero-norm embedding — invalid face crop.")
    return (output / norm).tolist()


def extract_embedding(image: np.ndarray) -> list:
    """
    Full pipeline: detect face → align to 112×112 → extract 512-d embedding.

    Raises ValueError if no face is detected (mirrors DeepFace enforce_detection=True).
    Uses the highest-confidence face if multiple are detected.
    """
    faces = detect_faces(image)
    if not faces:
        raise ValueError("No face detected in the image.")

    best = faces[0]  # highest score
    face_crop = align_face(image, best["kps"])
    return get_embedding(face_crop)
