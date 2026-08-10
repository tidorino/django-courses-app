# ---- Stage 1: build Tailwind CSS -------------------------------------------------
FROM node:20-alpine AS css-builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY tailwind.config.js ./
COPY static_src ./static_src
COPY templates ./templates
COPY core/templates ./core/templates
RUN npm run build

# ---- Stage 2: Python/Django app ---------------------------------------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=css-builder /app/static/css/styles.css ./static/css/styles.css

RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
