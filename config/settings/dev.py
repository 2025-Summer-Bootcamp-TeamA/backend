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

GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")