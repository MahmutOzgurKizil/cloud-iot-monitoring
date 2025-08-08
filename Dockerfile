FROM python:3.9-slim

WORKDIR /leaderboard-project/application

COPY application/requirements.txt .
RUN pip install -r requirements.txt

COPY application/ .

EXPOSE 5000

CMD ["python", "app.py"]
