from .base import *

# PyMySQL을 MySQLdb로 사용하도록 설정
import pymysql
pymysql.install_as_MySQLdb()

DEBUG = False
ALLOWED_HOSTS = ["*"]


# 환경변수에서 데이터베이스 설정 가져오기
DB_TYPE = os.getenv('DB_TYPE', 'mysql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD')
if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD 환경 변수는 필수로 설정되어야 합니다.")
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
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINES[DB_TYPE],
            'NAME': BASE_DIR / DB_NAME,
        }
    }
else:
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

CORS_ORIGIN_ALLOW_ALL = False

# HTTPS 보안 설정 (Traefik 뒤에서 실행될 때)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Traefik에서 리다이렉트 처리

# 추가 HTTPS 보안 설정
SECURE_HSTS_SECONDS = 31536000  # 1년 (HSTS: HTTP Strict Transport Security)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # 서브도메인에도 HSTS 적용
SECURE_HSTS_PRELOAD = True  # HSTS preload 리스트 포함 가능
SECURE_CONTENT_TYPE_NOSNIFF = True  # MIME 타입 스니핑 방지
SECURE_BROWSER_XSS_FILTER = True  # XSS 필터 활성화
SESSION_COOKIE_SECURE = True  # 세션 쿠키 HTTPS 전용
CSRF_COOKIE_SECURE = True  # CSRF 쿠키 HTTPS 전용