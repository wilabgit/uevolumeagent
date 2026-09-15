#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  cat <<'EOF'
Usage: ./run-agent-client-30.sh <llm-model> [--timeout N] [--reference_output "..."]

Example:
  ./run-agent-client-30.sh ollama-7b --timeout 60 --reference_output "ues: 100, usage: 50GB"
EOF
  exit 1
fi

LLM_MODEL="$1"
OUTPUT_CSV="results_2ues_oneshotReports_${LLM_MODEL}_newkey.csv"
OUTPUT_LOG="log_${LLM_MODEL}.log"
WEBHOOK_URL="http://jetson:8000/langGraph-webhook"
PROMPT="get the number of ues connected to the network and the usage volume from last report"
#PROMPT="From the most recent report, for connected UEs, provide the total UE count and per-UE data usage volume."
shift 1
EXTRA_ARGS=("$@")

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT
rm -f "$OUTPUT_CSV"
rm -f "$OUTPUT_LOG"

for i in $(seq 1 30); do
  echo "Run $i/30"
  python3 agent-client.py --url "$WEBHOOK_URL" --ollama_model "$LLM_MODEL" --session "$LLM_MODEL--$i" --prompt "$PROMPT" --output csv --output_file "$OUTPUT_CSV" ${EXTRA_ARGS[@]} > "$TMPFILE"
  if [[ $i -eq 26 ]]; then
    cat "$TMPFILE" > "$OUTPUT_LOG"
  else
    tail -n +2 "$TMPFILE" >> "$OUTPUT_LOG"
  fi
  echo "  appended results to $OUTPUT_LOG"
  sleep 5
done

echo "✅ Combined CSV written to $OUTPUT_CSV"
