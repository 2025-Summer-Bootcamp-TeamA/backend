import os
import sys
from pathlib import Path
from decouple import config
from dotenv import load_dotenv
from google.oauth2 import service_account
from datetime import timedelta

# PyMySQL을 MySQLdb로 사용하도록 설정
import pymysql
pymysql.install_as_MySQLdb()

# .env 로드
load_dotenv()

# 프로젝트 최상위 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# 시크릿 키 - 환경변수가 없으면 애플리케이션 시작 불가
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

# 개발용 설정 - 환경변수로 제어
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ALLOWED_HOSTS 설정 - 환경변수로 제어
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
if DEBUG:
    ALLOWED_HOSTS.extend(['hiedu.site', 'api.hiedu.site'])

# Traefik 등의 프록시 환경에서 HTTPS 인식용
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# 앱 등록
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    # 내부 앱
    'apps.videos',
    'apps.avatars',
    'apps.gcs',
    'apps.core',
    'apps.authentication',
    'apps.place',
    # 외부 라이브러리
    'rest_framework',
    'drf_yasg',
    'storages',
]

# 미들웨어
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.authentication.middleware.JWTAuthDebugMiddleware',  # 디버깅용
]

# URL 설정
ROOT_URLCONF = 'config.urls'

# 템플릿 설정
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

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

# 국제화
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# 정적 파일
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# 미디어 파일
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 기본 필드 타입
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

# Google Cloud Storage 설정
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": os.getenv("GS_BUCKET_NAME"),
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Google 서비스 계정 자격증명 로딩
google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if google_credentials_path and os.path.exists(google_credentials_path):
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
        google_credentials_path
    )
    # STORAGES에 credentials 추가
    STORAGES["default"]["OPTIONS"]["credentials"] = GS_CREDENTIALS
else:
    GS_CREDENTIALS = None
    if DEBUG:
        print("Warning: Google Cloud credentials not found. Some features may not work.")

# 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG' if DEBUG else 'INFO',
    },
}

# REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.authentication.authentication.CustomJWTAuthentication',
    ],
}

# JWT 설정
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

# CORS 설정 - 환경변수로 제어
CORS_ORIGIN_ALLOW_ALL = os.getenv("CORS_ORIGIN_ALLOW_ALL", "False").lower() == "true"
if not CORS_ORIGIN_ALLOW_ALL:
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
CORS_ALLOW_CREDENTIALS = True

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VISIONSTORY_API_KEY = config("VISIONSTORY_API_KEY", default="")

# Smithery MCP 설정
SMITHERY_API_KEY = config("SMITHERY_API_KEY", default="")

# Brave MCP 설정
BRAVE_MCP_BASE_URL = config("BRAVE_MCP_BASE_URL", default="")
BRAVE_API_KEY = config("BRAVE_API_KEY", default="")
BRAVE_MCP_PROFILE = config("BRAVE_MCP_PROFILE", default="default")

# Fetch MCP 설정
FETCH_MCP_BASE_URL = config("FETCH_MCP_BASE_URL", default="")
FETCH_API_KEY = config("FETCH_API_KEY", default="")
FETCH_MCP_PROFILE = config("FETCH_MCP_PROFILE", default="default")

# RabbitMQ 연결 설정 (환경변수 또는 기본값)
RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS', 'guest')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@rabbitmq:5672//')

if RABBITMQ_USER == 'guest' and RABBITMQ_PASS == 'guest' and DEBUG:
    print("WARNING: RabbitMQ using default guest credentials! Change for production.")

# Redis 비밀번호가 설정되지 않은 경우 기본 연결 사용 (개발 환경용)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
if REDIS_PASSWORD:
    CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@redis:6379/0"
else:
    CELERY_RESULT_BACKEND = "redis://redis:6379/0"
    if DEBUG:
        print("WARNING: Redis running without password protection!")

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul'
