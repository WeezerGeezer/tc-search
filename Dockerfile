FROM python:3.11-slim

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# Install system dependencies and Cloud SQL Proxy
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Cloud SQL Proxy
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy \
    && chmod +x cloud_sql_proxy

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

# Start Cloud SQL Proxy and run the application
CMD ./cloud_sql_proxy -instances=${INSTANCE_CONNECTION_NAME}=tcp:3306 & \
    sleep 5 && \
    gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 search_site.app:app
