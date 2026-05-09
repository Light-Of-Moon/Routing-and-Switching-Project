FROM python:3.9-slim

WORKDIR /app

# Install system dependencies, including docker client so the app can manage other containers
RUN apt-get update && apt-get install -y \
    docker.io \
    iptables \
    nmap \
    iputils-ping \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the Flask app listens on all interfaces
ENV FLASK_APP=real_dashboard.py
ENV FLASK_ENV=development

# Expose the new port
EXPOSE 5001

CMD ["python", "real_dashboard.py"]
