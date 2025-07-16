# Initial-settings
초기 세팅과 관련된 레포지토리 (UV 사용)

## UV 설치
UV는 Rust로 작성된 빠른 Python 패키지 매니저입니다.

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Homebrew (macOS)
brew install uv

# 설치 확인
uv --version
```

## 가상환경 및 패키지 관리
UV는 가상환경을 자동으로 생성하고 관리합니다.

<details>
<summary><strong>1. 프로젝트 설정</strong></summary>

```bash
# 프로젝트 의존성 설치 (가상환경 자동 생성)
uv sync

# 개발 도구 포함 설치
uv sync --extra dev
```

UV가 자동으로 `.venv` 가상환경을 생성하고 활성화합니다.

</details>

---

<details>
<summary><strong>2. 패키지 추가/제거</strong></summary>

```bash
# 패키지 추가
uv add django
uv add djangorestframework

# 패키지 제거  
uv remove package-name
```

</details>

---

<details>
<summary><strong>3. 환경 동기화</strong></summary>

```bash
# lock 파일 기준으로 정확한 의존성 설치
uv sync --frozen

# 의존성 업데이트
uv sync --upgrade
```

</details>

## 패키지 설치
pyproject.toml 파일에 정의된 패키지들을 설치하는 방법

<details>
<summary><strong>1. 패키지 설치</strong></summary>

```bash
# 기본 의존성 설치
uv sync

# 개발 의존성 포함 설치
uv sync --extra dev
```

</details>

---

## uv.lock 파일 관리
uv.lock은 모든 의존성의 정확한 버전을 고정하는 중요한 파일입니다.

<details>
<summary><strong>1. uv.lock이란?</strong></summary>

**uv.lock 파일의 역할:**
- 📦 **모든 의존성의 정확한 버전 기록**
- 🔒 **재현 가능한 빌드 보장** 
- 🛡️ **패키지 해시값으로 보안 검증**

```bash
# uv.lock 파일은 자동으로 생성됩니다
uv add django          # pyproject.toml + uv.lock 업데이트
uv sync --upgrade      # 의존성 업데이트 시 uv.lock 갱신
```

</details>

---

<details>
<summary><strong>2. 충돌 해결</strong></summary>

**uv.lock 파일 문제가 발생했을 때:**

```bash
# 1. lock 파일 재생성
rm uv.lock
uv lock

# 2. 의존성 동기화
uv sync

# 3. 의존성 강제 업데이트
uv sync --upgrade

# 4. lock 파일 검증
uv sync --check
```

</details>

---

## Docker로 DB 띄우기
docker-compose.yml 파일을 통해 Docker로 DB를 띄우는 방법입니다. 
이 예시에서는 MySQL을 사용합니다.

파이참 유료버전을 쓸 경우 yml 파일을 열면 Docker로 DB를 띄우는 버튼이 있습니다.

해당 버튼을 눌러 DB를 띄우고 파이참 우측 상단의 DB 탭에서 DB에 접속할 수 있습니다.

<details>
<summary><strong>1. Docker로 DB 띄우기</strong></summary>

- Docker로 DB 띄우기  
  ```bash
  docker compose up --build -d
  ```
- Docker로 DB 중지하기  
  ```bash
  docker compose down
  ```
</details>

<br>

## Django 프로젝트 생성
<details>
<summary><strong>1. Django 프로젝트 생성</strong></summary>

- Django 프로젝트 생성  
  ```bash
  uv run django-admin startproject config .
  ```
- Django 앱 생성  
  ```bash
  uv run python manage.py startapp app_name
  ```
</details>

---

<details>
<summary><strong>2. Django 프로젝트 실행</strong></summary>

- Django 프로젝트 마이그레이션  
  ```bash
  uv run python manage.py makemigrations
  uv run python manage.py migrate
  ```

- Django 프로젝트 실행  
  ```bash
  uv run python manage.py runserver
  ```
  
</details>

