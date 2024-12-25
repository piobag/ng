FROM python:3.10-slim

ENV FLASK_ENV production

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY api api

EXPOSE 5000
ENTRYPOINT ["gunicorn", "--worker-tmp-dir=/dev/shm", "-w2", "--threads=4", "-k", "gthread", "--reload", "--timeout=60", "-b:5000", "--access-logfile=-", "--error-logfile=-", "api:create_app()"]
