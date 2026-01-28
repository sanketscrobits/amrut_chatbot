FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps for packages that may need compilation (adjust as needed)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata first to leverage Docker cache
COPY pyproject.toml ./
COPY README.md ./

# Copy source
COPY src ./src

# Upgrade pip & install project
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

EXPOSE 8000

# Start the app with uvicorn
CMD ["uvicorn", "src.main.chatbotapi:app", "--host", "0.0.0.0", "--port", "8000"]
