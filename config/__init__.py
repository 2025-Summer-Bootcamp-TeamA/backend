try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery가 설치되지 않은 경우 (개발 환경 등)
    celery_app = None
    __all__ = ()
