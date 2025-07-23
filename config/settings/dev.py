import os
from .base import *
from dotenv import load_dotenv
from google.oauth2 import service_account

# PyMySQL을 MySQLdb로 사용하도록 설정
import pymysql
pymysql.install_as_MySQLdb()

env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

DEBUG = True
ALLOWED_HOSTS = ["*"]

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