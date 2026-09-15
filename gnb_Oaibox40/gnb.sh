#!/bin/bash

# =========================
# Config
# =========================
WORKDIR="/home/user/openairinterface5g"
BUILD_DIR="cmake_targets/ran_build/build"
CONFIG_FILE="/home/user/openairinterface5g/targets/PROJECTS/GENERIC-NR-5GC/CONF/oaibox.yaml"
mkdir -p "$(pwd)/start-log"
LOGFILE="$(pwd)/start-log/start_gnb_$(date +%Y%m%d_%H%M%S).log"

# =========================
# Logging functions
# =========================
log() {
  echo "[ $(date '+%Y-%m-%d %H:%M:%S') ] $1" | tee -a "$LOGFILE"
}

run_cmd() {
  log ">>> $*"
  "$@" 2>&1 | tee -a "$LOGFILE"
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log "❌ Errore durante l'esecuzione del comando"
    exit 1
  fi
}

# =========================
# Start
# =========================
log "🚀 Avvio script start gNB (OAIBOX)"

#Restore config file for gNB 
run_cmd cp "/home/user/openairinterface5g/targets/PROJECTS/GENERIC-NR-5GC/CONF/prez_oaibox.yaml" "$CONFIG_FILE"  

# =========================
# Routing
# =========================
log "🛣️  Configurazione rotte verso 5GC"

sudo ip route replace 192.168.70.0/24 via 192.168.2.2
sudo ip route replace 192.168.72.0/24 via 192.168.2.2
sudo ip route replace 192.168.73.0/24 via 192.168.2.2

# =========================
# OpenAirInterface env
# =========================
cd "$WORKDIR" || { log "❌ Directory OAI non trovata"; exit 1; }
log "📁 Directory corrente: $(pwd)"

log "🌱 Sourcing oaienv"
# shellcheck disable=SC1091
source oaienv

cd "$BUILD_DIR" || { log "❌ Directory build gNB non trovata"; exit 1; }
log "📁 Directory build: $(pwd)"

# =========================
# Start gNB
# =========================
log "📡 Avvio nr-softmodem (SA mode)"

log "⚠️  Il processo rimarrà in foreground"
log "⚠️  Usa CTRL+C per terminare"

sudo ./nr-softmodem \
  -O "$CONFIG_FILE" \
  --sa 2>&1 | tee -a "$LOGFILE"

log "🛑 gNB terminato"


