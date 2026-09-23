FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/app/.hf
WORKDIR /app

# CPU-only torch first: the default PyPI wheel on x86 bundles CUDA (several GB).
# requirements.txt then sees torch==2.9.1 as already satisfied.
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image so workers never download it at runtime.
RUN python -c "from sentence_transformers import SentenceTransformer as S; S('all-MiniLM-L6-v2')"

COPY . .
RUN SECRET_KEY=collectstatic DEBUG=False python manage.py collectstatic --noinput

RUN useradd --create-home app && mkdir -p media && chown -R app /app
USER app

EXPOSE 8000
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
