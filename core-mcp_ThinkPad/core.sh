#!/bin/bash

# =========================
# Config
# =========================
WORKDIR="/home/federico/oai-cn5g-fed-master/docker-compose"
COMPOSE_FILE="docker-compose-basic-vpp-nrf.yaml"
mkdir -p "$(pwd)/start-log"
LOGFILE="$(pwd)/start-log/start_5g_core_$(date +%Y%m%d_%H%M%S).log"

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
log "🚀 Avvio script setup OAI CN5G"

# Move to working directory
cd "$WORKDIR" || { log "❌ Directory non trovata"; exit 1; }
log "📁 Directory corrente: $(pwd)"

# Docker compose up
run_cmd docker compose -f "$COMPOSE_FILE" up -d

log "⏳ Attendere che tutti i container siano healthy..."
sleep 30

# Show running containers
run_cmd docker ps


# Flush raw PREROUTING table
run_cmd sudo iptables -t raw -F PREROUTING

# =========================
# DOCKER-USER rules
# =========================
log "🧱 Configurazione regole iptables (DOCKER-USER)"

run_cmd sudo iptables -A DOCKER-USER -s 192.168.2.0/24 -d 192.168.70.0/24 -j ACCEPT
run_cmd sudo iptables -A DOCKER-USER -s 192.168.2.0/24 -d 192.168.72.0/24 -j ACCEPT
run_cmd sudo iptables -A DOCKER-USER -s 192.168.2.0/24 -d 192.168.73.0/24 -j ACCEPT

run_cmd sudo iptables -A DOCKER-USER -d 192.168.2.0/24 -s 192.168.70.0/24 -j ACCEPT
run_cmd sudo iptables -A DOCKER-USER -d 192.168.2.0/24 -s 192.168.72.0/24 -j ACCEPT
run_cmd sudo iptables -A DOCKER-USER -d 192.168.2.0/24 -s 192.168.73.0/24 -j ACCEPT

# Show rules
log "📜 Regole attuali DOCKER-USER:"
run_cmd sudo iptables -L DOCKER-USER -nv

#ngix proxy is placed between smf and Flask callback's report server to convert http2 in http1 
run_cmd docker exec -it oai-smf update-ca-certificates

log "✅ Script completato con successo"
log "📄 Log salvato in: $LOGFILE"
