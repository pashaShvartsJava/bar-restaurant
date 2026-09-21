FROM python:3.12-slim
LABEL authors="ctrad"

WORKDIR /payment_service
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000

CMD ["uvicorn", "payment_service.main:app", "--host", "0.0.0.0", "--port", "8008", "--reload"]