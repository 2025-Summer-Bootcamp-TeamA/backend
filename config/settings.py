import os
from pathlib import Path
from dotenv import load_dotenv

# PyMySQL을 MySQLdb로 사용하도록 설정
import pymysql
pymysql.install_as_MySQLdb()

# .env 로드
load_dotenv()

# 프로젝트 최상위 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# API 키
VISIONSTORY_API_KEY = os.getenv("VISIONSTORY_API_KEY")  # 반드시 .env에 설정되어 있어야 함!
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 시크릿 키 (실제 배포 시에는 환경변수에서 가져오는 방식으로 바꿔야 함)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-q6z$d70f^g6b!=wcuk^$bntvd!p1^-n0pxlmg_c*a_vu0nlvj9')

# 개발용 설정
DEBUG = True
ALLOWED_HOSTS = []

# 앱 등록
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 내부 앱
    'apps.avatars',
    'apps.posts',

    # 외부 라이브러리
    'rest_framework',
    'drf_yasg',
    'storages',
    'apps.authentication',
    'place'
]

# 미들웨어
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

# 국제화
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 정적 파일
STATIC_URL = 'static/'

# 미디어 파일
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 기본 필드 타입
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
