FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy repository
COPY . .

# Install Python dependencies using pip install -e .
RUN pip install --no-cache-dir -e .

# Create logs directory
RUN mkdir -p logs

# Expose port for OpenEnv server (7860 for HuggingFace Spaces)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run FastAPI server with uvicorn
CMD ["uvicorn", "inference:app", "--host", "0.0.0.0", "--port", "7860"]
