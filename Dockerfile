FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code, static assets, and unified runner
COPY app/ ./app/
COPY static/ ./static/
COPY run.py .

EXPOSE 8000

# Zero-configuration entrypoint
ENTRYPOINT ["python", "run.py"]
