# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Install git and required system dependencies
RUN apt-get update && \
    apt-get install -y git librdkafka-dev gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/upload_api/templates

# Copy API files
COPY api_script/main.py /app/upload_api/
COPY api_script/facade.py /app/upload_api/
COPY api_script/requirements.txt /app/upload_api/
COPY api_script/templates/upload.html /app/upload_api/templates/

# Install Python dependencies
WORKDIR /app/upload_api
RUN pip install --no-cache-dir -r requirements.txt

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV KAFKA_BOOTSTRAP_SERVERS=kafka-service.default.svc.cluster.local:9092

# Expose the port
EXPOSE 8000

# Set the entry point
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]