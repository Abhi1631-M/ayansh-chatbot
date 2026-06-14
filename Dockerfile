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

# Initialize the databases during the build phase
# This bakes the default products and the language model into the Docker image,
# so it works immediately on cloud platforms without Persistent Disks.
RUN python -m database.init_db
RUN python -m database.sync_vectors

# Expose the port Uvicorn will run on
EXPOSE 8000

# Start the FastAPI application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
