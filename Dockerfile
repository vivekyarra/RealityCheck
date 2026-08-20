FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN addgroup --system realitycheck && adduser --system --ingroup realitycheck realitycheck

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY README.md ./
RUN mkdir -p /app/.realitycheck && chown -R realitycheck:realitycheck /app

USER realitycheck
EXPOSE 8080

CMD ["sh", "-c", "gunicorn app.main:app --bind 0.0.0.0:${PORT} --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --access-logfile -"]
