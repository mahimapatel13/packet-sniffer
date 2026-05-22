FROM python:3.10-slim

# Install system dependencies required for compilation and packet capturing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/

# Expose FastAPI standard port
EXPOSE 8000

# Execute server using uvicorn
CMD ["python", "app/main.py"]
