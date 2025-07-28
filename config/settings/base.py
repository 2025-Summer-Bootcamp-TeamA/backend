import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# PyMySQL을 MySQLdb로 사용하도록 설정
import pymysql
pymysql.install_as_MySQLdb()

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-key")

# API 키
VISIONSTORY_API_KEY = os.getenv("VISIONSTORY_API_KEY")  # 반드시 .env에 설정되어 있어야 함!

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
    "apps.core",
    "rest_framework",
    "apps.authentication",
    "drf_yasg",
    "apps.place",
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

# Traefik 등의 프록시 환경에서 HTTPS 인식용
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

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

# 데이터베이스 설정 (환경변수 기반)
# 환경변수에서 데이터베이스 설정 가져오기
DB_TYPE = os.getenv('DB_TYPE', 'mysql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'teama_db')

# 데이터베이스 엔진 매핑
DB_ENGINES = {
    'postgresql': 'django.db.backends.postgresql',
    'mysql': 'django.db.backends.mysql',
    'sqlite3': 'django.db.backends.sqlite3',
    'oracle': 'django.db.backends.oracle',
}

# 데이터베이스 설정 구성
if DB_TYPE == 'sqlite3':
    # SQLite의 경우 파일 경로 사용
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINES[DB_TYPE],
            'NAME': BASE_DIR / DB_NAME,
        }
    }
else:
    # PostgreSQL, MySQL 등의 경우 서버 연결 정보 사용
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINES.get(DB_TYPE, DB_ENGINES['mysql']),
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
    }

# 비밀번호 검증기
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

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
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,  # <- Explicitly use stdout
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    # 'loggers': {
    #     # HTTP 요청 로그 끄기
    #     'httpx': {
    #         'level': 'WARNING',
    #         'handlers': ['console'],
    #     },
    #     'httpcore': {
    #         'level': 'WARNING',
    #         'handlers': ['console'],
    #     },
    #     'urllib3': {
    #         'level': 'WARNING',
    #         'handlers': ['console'],
    #     },
    #     'requests': {
    #         'level': 'WARNING',
    #         'handlers': ['console'],
    #     },
    # },
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

# JWT 설정
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',
}

# Smithery MCP 설정
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY", "")

# Brave MCP 설정
BRAVE_MCP_BASE_URL = os.getenv("BRAVE_MCP_BASE_URL", "")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
BRAVE_MCP_PROFILE = os.getenv("BRAVE_MCP_PROFILE", "default")

# Fetch MCP 설정
FETCH_MCP_BASE_URL = os.getenv("FETCH_MCP_BASE_URL", "")
FETCH_API_KEY = os.getenv("FETCH_API_KEY", "")

# REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.authentication.authentication.CustomJWTAuthentication',
    ],
}

