import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-key")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "apps.videos",
    "apps.avatars",
    "apps.gcs",
    "rest_framework",
    "apps.authentication",
    "drf_yasg",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Swagger basePath 제거를 위한 설정
FORCE_SCRIPT_NAME = None

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        }
    },
    "USE_SESSION_AUTH": False,
    "DEFAULT_INFO": "config.urls.api_info",
    "DOC_EXPANSION": "none",
    "DEEP_LINKING": True,
    "SPEC_URL": None,  # basePath 자동 감지 비활성화
}

INSTALLED_APPS += ["storages"]


STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": os.getenv("GS_BUCKET_NAME"),
            # credentials는 dev.py에서 GS_CREDENTIALS로 정의됨
            # "credentials": GS_CREDENTIALS,  # dev.py에서만 추가
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        # HTTP 요청 로그 끄기
        'httpx': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
        'httpcore': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
        'urllib3': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
        'requests': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
    },
}

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# RabbitMQ 연결 설정 (환경변수 또는 기본값)
RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS', 'guest')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@rabbitmq:5672//')

if RABBITMQ_USER == 'guest' and RABBITMQ_PASS == 'guest':
    print("WARNING: RabbitMQ using default guest credentials! Change for production.")
# Redis 비밀번호가 설정되지 않은 경우 기본 연결 사용 (개발 환경용)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
if REDIS_PASSWORD:
    CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@redis:6379/0"
else:
    CELERY_RESULT_BACKEND = "redis://redis:6379/0"
    print("WARNING: Redis running without password protection!")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul'
