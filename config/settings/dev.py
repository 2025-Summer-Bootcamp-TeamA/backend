import os
from .base import *
from dotenv import load_dotenv
from google.oauth2 import service_account

env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CORS_ORIGIN_ALLOW_ALL = True

# Google 서비스 계정 자격증명 로딩
google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if google_credentials_path and os.path.exists(google_credentials_path):
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
        google_credentials_path
    )
else:
    GS_CREDENTIALS = None
    # 개발 환경에서는 로그로 알림
    print("Warning: Google Cloud credentials not found. Some features may not work.")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")