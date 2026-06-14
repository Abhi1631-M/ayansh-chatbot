# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Ensure sentence-transformers caches models inside the container
ENV HF_HOME=/app/.cache/huggingface

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the seed database and vectors during build (baked into image as a template)
RUN python -m database.seed
RUN python -m database.sync_vectors

# Create persistent data directory (HF Spaces mounts /data for persistence)
RUN mkdir -p /data

# Expose the port Uvicorn will run on (Hugging Face Spaces requires 7860)
EXPOSE 7860

# Use entrypoint script to copy seed data to /data on first boot
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
