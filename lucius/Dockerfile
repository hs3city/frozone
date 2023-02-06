FROM mcr.microsoft.com/playwright/python:v1.30.0-jammy

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY lucius.py /app/

CMD ["python", "/app/lucius.py"]
