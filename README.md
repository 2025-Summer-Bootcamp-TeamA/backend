# TeamA - Django REST API 프로젝트
Django REST Framework 기반의 백엔드 API 프로젝트 (pip 사용)

## 환경 설정

### 1. Python 및 가상환경 설정
Python 3.11 이상이 필요합니다.

```bash
# Python 버전 확인
python --version

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows
```

### 2. 의존성 설치

<details>
<summary><strong>개발 환경 설정</strong></summary>

```bash
# 개발 의존성 설치 (테스트, 린팅 도구 포함)
pip install -r requirements-dev.txt

# 또는 Makefile 사용
make dev
```

</details>

<details>
<summary><strong>운영 환경 설정</strong></summary>

```bash
# 운영 의존성 설치
pip install -r requirements-prod.txt

# 또는 Makefile 사용
make prod
```

</details>

<details>
<summary><strong>기본 설치</strong></summary>

```bash
# 기본 의존성만 설치
pip install -r requirements.txt

# 또는 Makefile 사용
make install
```

</details>

## 패키지 관리

### 의존성 파일 구조
```
requirements.txt         # 기본 의존성
requirements-dev.txt    # 개발 환경 의존성 (테스트, 린팅 등)
requirements-prod.txt   # 운영 환경 의존성 (gunicorn, whitenoise)
```

<details>
<summary><strong>패키지 추가/제거</strong></summary>

```bash
# 새 패키지 설치
pip install package-name

# requirements.txt에 추가
echo "package-name>=1.0.0" >> requirements.txt

# 또는 Makefile 사용
make deps-add PKG=package-name

# 패키지 제거
pip uninstall package-name

# 또는 Makefile 사용
make deps-remove PKG=package-name
```

</details>

<details>
<summary><strong>의존성 동결</strong></summary>

```bash
# 현재 설치된 패키지 목록을 파일로 저장
pip freeze > requirements-frozen.txt

# 또는 Makefile 사용
make deps-freeze
```

</details>

## Makefile 명령어
프로젝트에서 자주 사용하는 명령어들을 간편하게 실행할 수 있습니다.

```bash
# 도움말 보기
make help

# 가상환경 생성
make venv

# 개발 환경 설정
make dev

# Django 서버 실행
make serve

# 데이터베이스 마이그레이션
make migrate

# 테스트 실행
make test

# 코드 포맷팅
make format

# 코드 린팅
make lint

# Django 셸 실행
make shell

# 슈퍼유저 생성
make superuser
```

## Docker로 DB 띄우기
docker-compose.yml 파일을 통해 Docker로 DB를 띄우는 방법입니다. 
이 예시에서는 MySQL을 사용합니다.

파이참 유료버전을 쓸 경우 yml 파일을 열면 Docker로 DB를 띄우는 버튼이 있습니다.

<details>
<summary><strong>Docker 명령어</strong></summary>

```bash
# Docker로 DB 띄우기
docker compose up --build -d

# Docker로 DB 중지하기
docker compose down

# 로그 확인
docker compose logs -f
```

</details>

## Django 프로젝트 실행

<details>
<summary><strong>1. 프로젝트 초기 설정</strong></summary>

```bash
# 가상환경 활성화
source venv/bin/activate

# 개발 의존성 설치
make dev

# 데이터베이스 마이그레이션
make migrate

# 슈퍼유저 생성 (선택사항)
make superuser
```

</details>

<details>
<summary><strong>2. 개발 서버 실행</strong></summary>

```bash
# Django 개발 서버 실행
make serve

# 또는 직접 실행
python manage.py runserver
```

서버가 실행되면 http://127.0.0.1:8000 에서 확인할 수 있습니다.

</details>

<details>
<summary><strong>3. 새 Django 앱 생성</strong></summary>

```bash
# Django 앱 생성
python manage.py startapp app_name

# 생성된 앱을 settings.py의 INSTALLED_APPS에 추가하세요
```

</details>

## 개발 도구

### 코드 품질 관리
```bash
# 코드 포맷팅 (Black + isort)
make format

# 코드 린팅 (flake8)
make lint

# 테스트 실행
make test
```

### 정적 파일 관리
```bash
# 정적 파일 수집
make collectstatic

# 또는 직접 실행
python manage.py collectstatic --noinput
```