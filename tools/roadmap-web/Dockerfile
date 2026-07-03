FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir fastapi "uvicorn[standard]"

COPY app.py .
COPY static/ static/

ENV ROADMAP_DB=/data/roadmap.db
EXPOSE 8090

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
