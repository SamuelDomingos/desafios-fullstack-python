FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production \
    HEADLESS=true \
    API_HOST=0.0.0.0 \
    API_PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    playwright install --with-deps chromium

COPY app ./app
COPY pyproject.toml README.md ./

EXPOSE 8000

CMD ["python", "-m", "app", "serve"]
