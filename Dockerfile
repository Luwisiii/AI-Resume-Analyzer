# One image: Django serves the API and the built React app from the same origin.
# Used by Render (render.yaml) and by docker-compose.yml.

FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FASTEMBED_CACHE_PATH=/app/.fastembed
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image so nothing downloads at runtime.
RUN python -c "from fastembed import TextEmbedding as T; T('sentence-transformers/all-MiniLM-L6-v2')"

COPY backend/ .
COPY --from=frontend /frontend/dist frontend_dist
RUN SECRET_KEY=collectstatic DEBUG=False python manage.py collectstatic --noinput

RUN useradd --create-home app && mkdir -p media && chown -R app /app
USER app

# PORT is set by Render; one worker with threads fits a 512 MB instance.
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 120"]
