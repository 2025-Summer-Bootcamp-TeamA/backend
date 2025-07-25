FROM python:3.11

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일만 먼저 복사 (캐시 최적화)
COPY requirements.txt ./

# 시스템 패키지 업데이트 및 의존성 설치
RUN apt-get update && apt-get clean
RUN pip install --upgrade pip && pip install -r requirements.txt

# 소스 코드 복사
COPY . .

# Django 서버 실행
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
