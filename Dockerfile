# Imagem de produção do Simples Frota (Django + Gunicorn)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Arquivos estáticos gerados na imagem e servidos pelo WhiteNoise
RUN DJANGO_SECRET_KEY=build DJANGO_DEBUG=False python manage.py collectstatic --noinput

# Usuário sem privilégios de root
RUN useradd --create-home appuser && mkdir -p /app/media && chown -R appuser /app
USER appuser

EXPOSE 8000

# Aplica as migrações e sobe o Gunicorn na porta definida pela plataforma
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --timeout 60 --access-logfile - --error-logfile -"]
