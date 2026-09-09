FROM python:3.12-slim

WORKDIR /app

# psycopg2 빌드용 (alembic이 sync 드라이버 사용)
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# 재현 가능한 설치: 실제 검증된 버전(requirements.lock)을 먼저 깔고, 패키지 자체는 의존성 없이 설치
COPY pyproject.toml requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps .

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
