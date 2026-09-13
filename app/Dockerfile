# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY migrations ./migrations
USER 10001
ENV PORT=8080
EXPOSE 8080
CMD ["python", "-u", "main.py"]
