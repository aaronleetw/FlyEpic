FROM python:3.9.18-slim-bookworm
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
