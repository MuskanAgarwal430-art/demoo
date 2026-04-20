import cv2
import numpy as np
import base64
import logging

logger = logging.getLogger(__name__)


def decode_base64_image(b64_string: str) -> np.ndarray:
    """Decode a base64 image string to a numpy BGR array."""
    if b64_string.startswith("data:image"):
        b64_string = b64_string.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_string)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image.")
    return image


def check_image_quality(image: np.ndarray) -> dict:
    """
    Basic quality checks on the raw frame: blur and brightness.
    Returns: {passed: bool, reason: str}
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 30:
        return {"passed": False, "reason": "Image is too blurry."}

    mean_brightness = gray.mean()
    if mean_brightness < 20:
        return {"passed": False, "reason": "Image is too dark."}
    if mean_brightness > 250:
        return {"passed": False, "reason": "Image is overexposed."}

    return {"passed": True, "reason": "OK"}


def recognize_face(b64_image: str, company_code: str) -> dict:
    """
    Full recognition pipeline:
      1. Decode base64 image
      2. Quality check
      3. Liveness check (MiniFAS)
      4. Detect face + align + extract 512-d ArcFace embedding (InsightFace ONNX)
      5. Search ChromaDB
    Returns a result dict.
    """
    from services.vector_db import ChromaDBService
    from ml.anti_spoof import check_liveness
    from ml.insightface_onnx import extract_embedding

    try:
        image = decode_base64_image(b64_image)
    except Exception as e:
        return {"success": False, "error": "invalid_image", "detail": str(e)}

    quality = check_image_quality(image)
    if not quality["passed"]:
        return {"success": False, "error": "poor_quality", "detail": quality["reason"]}

    liveness = check_liveness(image)
    if not liveness["is_live"]:
        return {"success": False, "error": "spoof_detected", "detail": "Liveness check failed."}

    try:
        embedding = extract_embedding(image)
    except Exception as e:
        logger.warning("InsightFace embedding failed: %s", e)
        return {"success": False, "error": "no_face_detected", "detail": str(e)}

    match = ChromaDBService.recognize(company_code, embedding)

    return {
        "success": True,
        "matched": match.get("matched", False),
        "employee_code": match.get("employee_code"),
        "employee_name": match.get("employee_name"),
        "confidence": match.get("confidence", 0.0),
        "distance": match.get("distance", 1.0),
        "liveness_confidence": liveness.get("confidence", 1.0),
        "reason": match.get("reason", ""),
    }
