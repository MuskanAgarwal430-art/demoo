import os
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

_session = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), "weights", "MiniFASNet.onnx")


def _get_session():
    global _session
    if _session is None:
        if not os.path.exists(MODEL_PATH):
            logger.warning("MiniFAS model not found at %s. Liveness check will be skipped.", MODEL_PATH)
            return None
        import onnxruntime as ort
        _session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    return _session


def _preprocess(image: np.ndarray, size: int = 80) -> np.ndarray:
    resized = cv2.resize(image, (size, size))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = rgb.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    normalized = (normalized - mean) / std
    # HWC → NCHW
    return normalized.transpose(2, 0, 1)[np.newaxis, :].astype(np.float32)


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x))
    return e / e.sum()


def check_liveness(image: np.ndarray) -> dict:
    """
    Run MiniFAS anti-spoofing.
    Returns: {is_live: bool, confidence: float}
    If model is missing, defaults to is_live=True (skip check).
    """
    session = _get_session()
    if session is None:
        return {"is_live": True, "confidence": 1.0, "skipped": True}

    try:
        input_data = _preprocess(image)
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: input_data})
        probs = _softmax(output[0][0])
        # Class 1 = live, class 0 = spoof
        is_live = bool(probs[1] > probs[0])
        confidence = float(probs[1])
        return {"is_live": is_live, "confidence": round(confidence, 4)}
    except Exception as e:
        logger.error("Liveness check error: %s", e)
        return {"is_live": True, "confidence": 1.0, "skipped": True}
