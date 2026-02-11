#!/bin/sh

# Verifica se o argumento "run_backup" foi fornecido
if [ "$1" != "run_backup" ]; then
  echo "Uso: ./backup.sh run_backup"
  echo "Para executar o backup, você precisa passar o argumento 'run_backup'."
  exit 0 # Sai silenciosamente, pois a intenção é não rodar sem o argumento
fi

# Variáveis
BACKUP_DIR="/dump"
TIMESTAMP=$(TZ=America/Sao_Paulo date +%F_%T)
BACKUP_FILE="mongo_ng_${TIMESTAMP}.dump"
ARCHIVE_FILE="${BACKUP_FILE}.tar.gz"
export HOST=$MONGO_HOST
export USER=$MONGO_USER
export PASS=$MONGO_PASS
export DB=$MONGO_AUTH_DB
export RCLONE_REMOTE="vultr"
export RCLONE_BUCKET_PATH="db-ng"
LOG_FILE="/var/log/mongo/backup.log"


# Definir variáveis de ambiente
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Configuração do msmtp
cat <<EOF > /etc/msmtprc
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile        /var/log/msmtp.log

account        default
host           $SMTP_SERVER
port           $SMTP_PORT
user           $SMTP_USER
password       $SMTP_PASS
from           $SMTP_USER
EOF

chmod 600 /etc/msmtprc

# Função para envio de email
send_email() {
  local subject="$1"
  local body="$2"
  (
    echo "Subject: $subject"
    echo "From: $SMTP_USER"
    echo "To: $EMAIL"
    echo ""
    echo "$body"
  ) | msmtp -a default $EMAIL
}

echo "Criando diretório de backup..."
mkdir -p "$BACKUP_DIR"

echo "Executando backup do MongoDB..."
/usr/bin/mongodump -h "$HOST" -u "$USER" -p "$PASS" --authenticationDatabase "$DB" --archive="$BACKUP_DIR/$BACKUP_FILE"

if [ $? -ne 0 ]; then
  echo "$(date '+%F %T') - ERRO: Falha NG-DB no mongodump" >> "$LOG_FILE"
  send_email "Falha NG-DB no Backup do MongoDB" "Erro ao fazer backup do MongoDB."
  rm -f "$BACKUP_DIR/$BACKUP_FILE"
  exit 1
fi

echo "Compactando arquivo de backup..."
tar -czvf "$BACKUP_DIR/$ARCHIVE_FILE" -C "$BACKUP_DIR" "$BACKUP_FILE"
rm -f "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -ne 0 ]; then
  echo "$(date '+%F %T') - ERRO: Falha NG-DB na compactação do arquivo" >> "$LOG_FILE"
  send_email "Falha NG-DB na Compactação do Backup do MongoDB" "Erro ao compactar o arquivo de backup."
  rm -f "$BACKUP_DIR/$ARCHIVE_FILE"
  exit 1
fi

echo "Enviando backup para a Object Storage via rclone..."
rclone copy --config /dev/null "$BACKUP_DIR/$ARCHIVE_FILE" "$RCLONE_REMOTE:$RCLONE_BUCKET_PATH"

if [ $? -ne 0 ]; then
  echo "$(date '+%F %T') - ERRO: Falha NG-DB ao enviar o backup com rclone" >> "$LOG_FILE"
  send_email "Falha NG-DB na Transferência com rclone" "Erro ao transferir o backup para o bucket do Object Storage."
  rm -f "$BACKUP_DIR/$ARCHIVE_FILE"
  exit 1
fi

# Se for meia-noite, salvar backup também como diário
HOUR=$(TZ=America/Sao_Paulo date +%H)
if [ "$HOUR" = "00" ]; then
  DAILY_NAME="mongo_ng_$(TZ=America/Sao_Paulo date +%F).dump.tar.gz"
  rclone copy --config /dev/null "$BACKUP_DIR/$ARCHIVE_FILE" "$RCLONE_REMOTE:$RCLONE_BUCKET_PATH/daily/$DAILY_NAME"
fi

echo "Removendo arquivos locais..."
rm -f "$BACKUP_DIR/$ARCHIVE_FILE"

echo "$(date '+%F %T') - SUCESSO: Backup NG-DB com sucesso e enviado para o Object Storage" >> "$LOG_FILE"
send_email "Backup do MongoDB NG-DB com Sucesso " "Backup gerado e enviado com sucesso para o Object Storage da Vultr."

echo "Backup NG-DB com sucesso."

# Limpar backups horários com mais de 24h
rclone lsjson --config /dev/null "$RCLONE_REMOTE:$RCLONE_BUCKET_PATH" --files-only \
  | jq -r --arg cutoff "$(date -u -d '1 day ago' --iso-8601=seconds)" \
    '.[] | select(.ModTime < $cutoff) | .Path' \
  | while read file; do
      rclone deletefile --config /dev/null "$RCLONE_REMOTE:$RCLONE_BUCKET_PATH/$file"
      echo "$(TZ=America/Sao_Paulo date '+%F %T') - INFO: Backup horário antigo removido: $file" >> "$LOG_FILE"
    done

# Limpar backups diários, manter apenas os 30 mais recentes
rclone lsjson --config /dev/null "$RCLONE_REMOTE:$RCLONE_BUCKET_PATH/daily" --files-only \
  | jq -r 'sort_by(.ModTime) | .[:-30] | .[].Path' \
  | while read file; do
      rclone deletefile --config /dev/null "$RCLONE_REMOTE:$RCLONE_BUCKET_PATH/daily/$file"
      echo "$(TZ=America/Sao_Paulo date '+%F %T') - INFO: Backup diário removido: $file" >> "$LOG_FILE"
    done