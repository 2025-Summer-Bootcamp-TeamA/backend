import os
from pathlib import Path
from dotenv import load_dotenv

# ✅ .env 로드
load_dotenv()

# ✅ 프로젝트 최상위 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ API 키
VISIONSTORY_API_KEY = os.getenv("VISIONSTORY_API_KEY")  # 반드시 .env에 설정되어 있어야 함!

# ✅ 시크릿 키 (실제 배포 시에는 환경변수에서 가져오는 방식으로 바꿔야 함)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-q6z$d70f^g6b!=wcuk^$bntvd!p1^-n0pxlmg_c*a_vu0nlvj9')

# ✅ 개발용 설정
DEBUG = True
ALLOWED_HOSTS = []

# ✅ 앱 등록
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ✅ 내부 앱
    'apps.avatars',
    'apps.posts',

    # ✅ 외부 라이브러리
    'rest_framework',
    'drf_yasg',
]

# ✅ 미들웨어
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ✅ URL 설정
ROOT_URLCONF = 'config.urls'

# ✅ 템플릿 설정
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ✅ 데이터베이스 (기본 SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ✅ 비밀번호 검증기
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ✅ 국제화
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ✅ 정적 파일
STATIC_URL = 'static/'

# ✅ 미디어 파일
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ✅ 기본 필드 타입
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
