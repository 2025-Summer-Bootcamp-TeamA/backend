FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 의존성 파일만 먼저 복사 (캐시 최적화)
COPY pyproject.toml uv.lock ./

# 시스템 패키지 업데이트 및 의존성 설치
RUN apt-get update && apt-get clean
RUN uv sync --frozen --no-dev

# 소스 코드 복사
COPY . .

# dotenv 설치 확인 (디버그용, 실패시 빌드 중단)
#RUN uv run python -c "import dotenv; print(dotenv.__version__)"

# Django 서버 실행
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
