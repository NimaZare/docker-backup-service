FROM python:3.11-slim

ENV TZ=Asia/Tehran

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron bash zip procps tzdata lftp \
    && ln -fs /usr/share/zoneinfo/Asia/Tehran /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backup.py /app/backup.py
COPY .env /app/.env
COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt && \
    touch /var/log/cron.log && \
    (echo "0 3 * * * /usr/local/bin/python /app/backup.py >> /var/log/cron.log 2>&1" | crontab -)

CMD ["cron", "-f"]
