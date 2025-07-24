FROM python:3.11

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get clean

# requirements 파일들 복사
COPY requirements.txt requirements-prod.txt ./

# pip 업그레이드 및 의존성 설치
RUN pip install --upgrade pip
RUN pip install -r requirements-prod.txt

# 소스 코드 복사
COPY . .

# Django 실행을 위한 환경 변수
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings.prod

# 기본 포트 노출
EXPOSE 8000

# Gunicorn을 사용하여 Django 서버 실행
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
