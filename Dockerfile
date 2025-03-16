FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .
RUN mkdir -p /data
VOLUME ["/data"]
ENV DB_FILE=/data/expenses.db
CMD ["python", "bot/bot_main.py"]
