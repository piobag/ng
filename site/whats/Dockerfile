FROM python:3
LABEL maintainer="Boragora <web@boragora.app>"



# Adding trusting keys to apt for repositories
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Adding Google Chrome to the repositories
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Updating apt to see and install Google Chrome
RUN apt-get -y update

# Magic happens
RUN apt-get install -y google-chrome-stable


RUN apt-get update                             \
 && apt-get install -y --no-install-recommends \
    ca-certificates curl firefox-esr           \
 && rm -fr /var/lib/apt/lists/*
 
# RUN curl -L https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz | tar xz -C /usr/local/bin \
#  && chmod +x /usr/local/bin/geckodriver

# RUN apt-get update -y \
# && apt-get install --no-install-recommends --no-install-suggests -y tzdata ca-certificates bzip2 curl wget libc-dev libxt6 \
# && apt-get install --no-install-recommends --no-install-suggests -y `apt-cache depends firefox-esr | awk '/Depends:/{print$2}'` \
# && update-ca-certificates \
# # Cleanup unnecessary stuff
# && apt-get purge -y --auto-remove \
#                 -o APT::AutoRemove::RecommendsImportant=false \
# && rm -rf /var/lib/apt/lists/* /tmp/*


# RUN FIREFOX_SETUP=firefox-setup.tar.bz2 && \
#     wget -O $FIREFOX_SETUP "https://download.mozilla.org/?product=firefox-95.0.1&os=linux64" && \
#     tar xjf $FIREFOX_SETUP -C /opt/ && \
#     ln -s /opt/firefox/firefox /usr/bin/firefox && \
#     rm $FIREFOX_SETUP
    
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /flask
COPY app ./app


ENTRYPOINT ["gunicorn", "--worker-tmp-dir=/dev/shm", "-w2", "--threads=4", "-k", "gthread", "--reload", "--timeout=120", "-b:5000", "--access-logfile=-", "--error-logfile=-", "app:app"]
EXPOSE 5000

# CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]

# RUN sed -i 's/app.json_encoder)$/JSONEncoder)/' /usr/local/lib/python3.10/site-packages/flask_mongoengine/json.py
