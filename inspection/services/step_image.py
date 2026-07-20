import base64
import io
import logging
import requests
from PIL import Image

logger = logging.getLogger("observability")


def get_step_image_base64(step) -> str:
    """
    Downloads the step image via CloudFront/HTTP (or reads it locally),
    converts it to JPEG format using Pillow, and returns its base64 encoded string.
    """
    if not step.file:
        raise ValueError(f"Step {step.id} has no file")

    file_url = step.file.url
    if file_url.startswith("http"):
        logger.info(
            f"Downloading step {step.id} image via CloudFront: {file_url}"
        )
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        file_bytes = response.content
    else:
        logger.info(f"Reading step {step.id} image directly from local storage")
        with step.file.open("rb") as f:
            file_bytes = f.read()

    # Convert format to JPEG (in case of WebP or PNG with alpha channels)
    try:
        image = Image.open(io.BytesIO(file_bytes))
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        jpeg_bytes = buffer.getvalue()
    except Exception as img_err:
        logger.error(
            f"Failed to convert step {step.id} image to JPEG: {img_err}"
        )
        raise

    return base64.b64encode(jpeg_bytes).decode("utf-8")
