FROM python:3.12-slim
LABEL authors="ctrad"

WORKDIR /user_service

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8005

CMD ["uvicorn", "user_service.main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]

