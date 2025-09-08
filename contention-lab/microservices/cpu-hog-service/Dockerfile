FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY hog.py .

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "hog.py"]