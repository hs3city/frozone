ARG PYTHON_VERSION=3.10.9

FROM python:$PYTHON_VERSION-slim

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

RUN useradd --create-home appuser
USER appuser

WORKDIR /home/appuser/bot

ENV PYTHONPATH=/home/appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
CMD ["python", "bot.py"]
