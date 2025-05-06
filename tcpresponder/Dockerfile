FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    git \
    libmariadb3 \
    libmariadb-dev \
    gcc \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

# First install ninjapy from local source
COPY . .

# Then install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip list

CMD ["python", "main.py"] 