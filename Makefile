# Django + UV 개발 자동화
.PHONY: help install dev sync serve migrate test lint format clean

help:  ## 도움말 표시
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 기본 의존성 설치
	uv sync

dev:  ## 개발 의존성 포함 설치
	uv sync --extra dev

sync:  ## 의존성 동기화 (lock 파일 기준)
	uv sync --frozen

serve:  ## Django 개발 서버 실행
	uv run python manage.py runserver

migrate:  ## 데이터베이스 마이그레이션
	uv run python manage.py makemigrations
	uv run python manage.py migrate

test:  ## 테스트 실행
	uv run pytest -v

lint:  ## 코드 린팅 (flake8)
	uv run flake8 .

format:  ## 코드 포맷팅 (black + isort)
	uv run black .
	uv run isort .

shell:  ## Django 셸 실행
	uv run python manage.py shell

superuser:  ## 슈퍼유저 생성
	uv run python manage.py createsuperuser

collectstatic:  ## 정적 파일 수집
	uv run python manage.py collectstatic --noinput

build:  ## 운영용 빌드
	uv sync --extra production
	$(MAKE) collectstatic

clean:  ## 캐시 및 임시 파일 정리
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov

deps-update:  ## 의존성 업데이트
	uv sync --upgrade

deps-tree:  ## 의존성 트리 표시
	uv tree

deps-add:  ## 새 패키지 추가 (사용법: make deps-add PKG=패키지명)
	uv add $(PKG)

deps-remove:  ## 패키지 제거 (사용법: make deps-remove PKG=패키지명)
	uv remove $(PKG) 