FROM python:3.11
LABEL maintainer="Boragora <web@boragora.app>"

RUN apt update && apt-get upgrade -y
RUN apt-get install -y wkhtmltopdf poppler-utils tesseract-ocr nano tmux curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /flask
COPY static ./static
COPY app ./app
COPY templates ./templates

ENTRYPOINT ["gunicorn", "--worker-tmp-dir=/dev/shm", "-w2", "--threads=4", "-k", "gthread", "--reload", "--timeout=120", "-b:5000", "--access-logfile=-", "--error-logfile=-", "app:create_app()"]
EXPOSE 5000

# CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]

# RUN sed -i 's/app.json_encoder)$/JSONEncoder)/' /usr/local/lib/python3.10/site-packages/flask_mongoengine/json.py