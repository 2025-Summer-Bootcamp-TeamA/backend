FROM python:3.11

# 작업 디렉토리 설정
WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# uv 프로젝트 파일들 복사 (의존성 정보)
COPY pyproject.toml uv.lock ./

# 시스템 패키지 업데이트 및 의존성 설치
RUN apt-get update && apt-get clean
RUN uv sync --frozen --no-dev

# 소스 코드 복사
COPY . .

# Django 실행을 위한 환경 변수
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings.dev

# 기본 포트 노출
EXPOSE 8000

# uv run을 사용하여 Django 서버 실행
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
