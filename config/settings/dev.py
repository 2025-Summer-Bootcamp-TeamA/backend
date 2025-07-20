from .base import *
from dotenv import load_dotenv
from decouple import config

env_path = os.path.join(BASE_DIR, "backend.env")
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

# Brave MCP 설정
BRAVE_MCP_BASE_URL = config("BRAVE_MCP_BASE_URL", default="")
BRAVE_API_KEY = config("BRAVE_API_KEY", default="")
BRAVE_MCP_PROFILE = config("BRAVE_MCP_PROFILE", default="default")

# Fetch MCP 설정
FETCH_MCP_BASE_URL = config("FETCH_MCP_BASE_URL", default="")
FETCH_API_KEY = config("FETCH_API_KEY", default="")