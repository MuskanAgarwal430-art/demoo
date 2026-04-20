import os
import uuid
from pathlib import Path
from django.conf import settings
from PIL import Image


def get_employee_image_dir(company_code: str, employee_code: str) -> Path:
    base = Path(settings.IMAGE_STORAGE_PATH)
    return base / company_code.upper() / employee_code


def save_face_image(company_code: str, employee_code: str, image_file) -> dict:
    """Save an uploaded image file. Returns {image_id, path, filename}."""
    img_dir = get_employee_image_dir(company_code, employee_code)
    img_dir.mkdir(parents=True, exist_ok=True)

    image_id = str(uuid.uuid4())
    ext = Path(image_file.name).suffix.lower() or ".jpg"
    filename = f"{image_id}{ext}"
    filepath = img_dir / filename

    img = Image.open(image_file)
    img = img.convert("RGB")
    img.save(str(filepath), "JPEG", quality=90)

    return {
        "image_id": image_id,
        "filename": filename,
        "path": str(filepath),
        "url": f"/media/faces/{company_code.upper()}/{employee_code}/{filename}",
    }


def list_employee_images(company_code: str, employee_code: str) -> list:
    img_dir = get_employee_image_dir(company_code, employee_code)
    if not img_dir.exists():
        return []
    images = []
    for f in sorted(img_dir.iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            images.append({
                "image_id": f.stem,
                "filename": f.name,
                "url": f"/media/faces/{company_code.upper()}/{employee_code}/{f.name}",
            })
    return images


def delete_employee_image(company_code: str, employee_code: str, image_id: str) -> bool:
    img_dir = get_employee_image_dir(company_code, employee_code)
    for f in img_dir.iterdir():
        if f.stem == image_id:
            f.unlink()
            return True
    return False


def delete_all_employee_images(company_code: str, employee_code: str):
    img_dir = get_employee_image_dir(company_code, employee_code)
    if img_dir.exists():
        for f in img_dir.iterdir():
            f.unlink()


def get_image_paths(company_code: str, employee_code: str) -> list:
    """Return full file paths of all images for an employee."""
    img_dir = get_employee_image_dir(company_code, employee_code)
    if not img_dir.exists():
        return []
    return [str(f) for f in sorted(img_dir.iterdir()) if f.suffix.lower() in (".jpg", ".jpeg", ".png")]
