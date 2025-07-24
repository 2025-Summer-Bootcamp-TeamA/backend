# Django + pip 개발 자동화
.PHONY: help install dev sync serve migrate test lint format clean venv

help:  ## 도움말 표시
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv:  ## 가상환경 생성
	python -m venv venv
	@echo "가상환경이 생성되었습니다. 'source venv/bin/activate' (Linux/Mac) 또는 'venv\\Scripts\\activate' (Windows)로 활성화하세요."

install:  ## 기본 의존성 설치
	pip install -r requirements.txt

dev:  ## 개발 의존성 포함 설치
	pip install -r requirements-dev.txt

prod:  ## 운영 의존성 포함 설치
	pip install -r requirements-prod.txt

serve:  ## Django 개발 서버 실행
	python manage.py runserver

migrate:  ## 데이터베이스 마이그레이션
	python manage.py makemigrations
	python manage.py migrate

test:  ## 테스트 실행
	pytest -v

lint:  ## 코드 린팅 (flake8)
	flake8 .

format:  ## 코드 포맷팅 (black + isort)
	black .
	isort .

shell:  ## Django 셸 실행
	python manage.py shell

superuser:  ## 슈퍼유저 생성
	python manage.py createsuperuser

collectstatic:  ## 정적 파일 수집
	python manage.py collectstatic --noinput

build:  ## 운영용 빌드
	$(MAKE) prod
	$(MAKE) collectstatic

clean:  ## 캐시 및 임시 파일 정리
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov

deps-freeze:  ## 현재 환경의 의존성을 requirements.txt로 저장
	pip freeze > requirements-frozen.txt

deps-upgrade:  ## pip 업그레이드
	pip install --upgrade pip

deps-add:  ## 새 패키지 추가 (사용법: make deps-add PKG=패키지명)
	pip install $(PKG)
	pip freeze > requirements-frozen.txt

deps-remove:  ## 패키지 제거 (사용법: make deps-remove PKG=패키지명)
	pip uninstall $(PKG) -y 