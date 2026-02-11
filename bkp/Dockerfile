FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências e repositório do MongoDB
RUN apt-get update && apt-get install -y \
    gnupg curl ca-certificates tzdata unzip jq && \
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    apt-get install -y mongodb-org-tools msmtp && \
    rm -rf /var/lib/apt/lists/*

# Instala rclone
RUN curl -LO https://downloads.rclone.org/rclone-current-linux-amd64.zip && \
    unzip rclone-current-linux-amd64.zip && \
    cp rclone-*-linux-amd64/rclone /usr/bin/ && \
    chmod 755 /usr/bin/rclone && \
    rm -rf rclone-*-linux-amd64 rclone-current-linux-amd64.zip

# Diretórios e script
RUN mkdir -p /var/log/mongo /dump
COPY rclone.sh /rclone.sh
RUN chmod +x /rclone.sh

CMD ["/rclone.sh"]