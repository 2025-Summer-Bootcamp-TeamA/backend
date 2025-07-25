# apps/core/services/ocr_service.py

from google.cloud import vision

def detect_text(path: str):
    """Detects text in the image file at `path` using Google Cloud Vision API."""
    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print("Texts:")

    for text in texts:
        print(f'\n"{text.description}"')
        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]
        print("bounds: {}".format(",".join(vertices)))

    if response.error.message:
        raise Exception(
            f"{response.error.message}\nFor more info: https://cloud.google.com/apis/design/errors"
        )
detect_text("/mnt/c/Users/k8947/OneDrive/바탕 화면/Incheon Univ/3학년/3학년 여름방학/bootcamp/backend/test_image01.png") #이곳에 이미지 주소를 넣으면 텍스트를 읽어옵니다.