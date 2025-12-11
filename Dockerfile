FROM python:3.10-slim

# System deps for Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr libtesseract-dev poppler-utils libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . /app

# Download spacy small model
RUN python -m spacy download en_core_web_sm

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
