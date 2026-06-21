FROM python:3.12-slim

WORKDIR /app

# System deps for postgres driver
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

COPY backend/ /app/backend/
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

