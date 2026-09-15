#!/bin/bash

# =========================
# Config
# =========================
WORKDIR="/home/user/openairinterface5g"
BUILD_DIR="cmake_targets/ran_build/build"
CONFIG_FILE="/home/user/openairinterface5g/targets/PROJECTS/GENERIC-NR-5GC/CONF/oaibox.yaml"
mkdir -p "./reset-log"
LOGFILE="./reset-log/reset_gnb_$(date +%Y%m%d_%H%M%S).log"

log() {
  echo "[ $(date '+%Y-%m-%d %H:%M:%S') ] $1" | tee -a "$LOGFILE"
}

run_cmd() {
  log ">>> $*"
  "$@" 2>&1 | tee -a "$LOGFILE"
}

log "🧹 RESET NETWORK gNB (OAIBOX)"

run_cmd cp "/home/user/openairinterface5g/targets/PROJECTS/GENERIC-NR-5GC/CONF/original_oaibox.yaml" "$CONFIG_FILE"

# =========================
# ROUTING
# =========================
log "🛣️  Rimozione rotte verso 5GC"

for NET in 192.168.70.0/24 192.168.72.0/24 192.168.73.0/24; do
  run_cmd sudo ip route del "$NET" 2>/dev/null
done

log "📜 Routing table finale:"
run_cmd ip route show

log "✅ Reset gNB completato"
log "📄 Log: $LOGFILE"
