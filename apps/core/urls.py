from django.urls import path
from .views import OCRView

urlpatterns = [
    path('', OCRView.as_view(), name='ocr'),  # ''로 두면 include 시 바로 /api/v1/ocr로 연결됨
]