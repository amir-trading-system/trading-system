FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    htop \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /main

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "make_container_alive.py"]
