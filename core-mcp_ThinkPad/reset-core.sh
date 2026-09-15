#!/bin/bash

# =========================
# Config
# =========================
WORKDIR="/home/federico/oai-cn5g-fed-master/docker-compose"
COMPOSE_FILE="docker-compose-basic-vpp-nrf.yaml"
mkdir -p "$(pwd)/reset-log"
LOGFILE="$(pwd)/reset-log/reset_core_$(date +%Y%m%d_%H%M%S).log"

log() {
  echo "[ $(date '+%Y-%m-%d %H:%M:%S') ] $1" | tee -a "$LOGFILE"
}

run_cmd() {
  log ">>> $*"
  "$@" 2>&1 | tee -a "$LOGFILE"
}

log "🧹 RESET NETWORK CORE (5GC)"

# =========================
# IPTABLES
# =========================
log "🔥 Reset iptables (filter)"

run_cmd sudo iptables -F DOCKER-USER

# =========================
# SHUTDOWN CORE
# =========================

# Move to working directory
cd "$WORKDIR" || { log "❌ Directory non trovata"; exit 1; }
log "📁 Directory corrente: $(pwd)"

log "🛣️ Bye Bye Core"
run_cmd docker compose -f "$COMPOSE_FILE" down

log "📜 Stato iptables dopo reset:"
run_cmd sudo iptables -L -nv
run_cmd sudo iptables -t nat -L -nv
run_cmd sudo iptables -t raw -L -nv

log "📜 Routing table finale:"
run_cmd ip route show

log "✅ Reset CORE completato"
log "📄 Log: $LOGFILE"
