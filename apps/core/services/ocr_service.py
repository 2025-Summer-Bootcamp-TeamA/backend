# apps/core/services/ocr_service.py

from google.cloud import vision

def detect_text(path: str):
    """Detects text in the image file at `path` using Google Cloud Vision API and returns results as a list of dicts."""
    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    result = []

    for text in texts:
        result.append({
            'description': text.description,
            'bounds': [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        })

    if response.error.message:
        raise Exception(
            f"{response.error.message}\nFor more info: https://cloud.google.com/apis/design/errors"
        )
    return result