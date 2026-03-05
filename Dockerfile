# Docker configuration for containerized deployment
FROM python:3.10-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL application files
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port 8000 (local / generic deployment)
EXPOSE 8000

# Set environment variable for port
ENV PORT=8000

# Run the application
CMD ["python", "app.py"]