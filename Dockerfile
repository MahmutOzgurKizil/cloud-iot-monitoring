FROM python:3.11-slim

WORKDIR /application

COPY application/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY application/ .

CMD ["python", "app.py"]
