#!/usr/bin/env python3
"""
n8n Chat Client — submits a prompt and reports latency + token usage.

Usage:
    python n8n_chat_client.py --url <webhook_url> --prompt "Your prompt here"

Options:
    --url       n8n Chat Trigger webhook URL (required)
    --prompt    Prompt text to send (required)
    --session   Session ID (optional; auto-generated if omitted)
    --timeout   Request timeout in seconds (default: 60)
    --output    Output format: table | json | csv (default: table)
"""

import argparse
import csv
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    sys.exit("❌  'requests' is not installed. Run: pip install requests")


# ── helpers ──────────────────────────────────────────────────────────────────

def extract_token_usage(response_body: dict) -> dict:
    """
    Walk the n8n response structure looking for token/usage fields.
    n8n AI-agent nodes may embed usage under different keys depending
    on the LLM provider (OpenAI, Anthropic, Gemini, …).
    Returns a normalised dict with prompt_tokens, completion_tokens, total_tokens.
    """
    usage = {
        "prompt_tokens":     None,
        "completion_tokens": None,
        "total_tokens":      None,
    }

    # Flatten the whole response into a single string search so we handle
    # arbitrary nesting (output[].usageMetadata, output[].usage, etc.)
    raw = json.dumps(response_body)

    # Try standard parse paths first
    candidates = [
        response_body,
        response_body.get("usage", {}),
        response_body.get("usageMetadata", {}),
        response_body.get("tokenUsageEstimate", {}),
    ]
    # Also check first item of any list value at top level
    for v in response_body.values():
        if isinstance(v, list) and v:
            item = v[0]
            if isinstance(item, dict):
                candidates.extend([
                    item,
                    item.get("usage", {}),
                    item.get("usageMetadata", {}),
                    item.get("tokenUsageEstimate", {}),
                    item.get("response", {}) if isinstance(item.get("response"), dict) else {},
                ])

    field_map = {
        # OpenAI / generic
        "prompt_tokens":            "prompt_tokens",
        "completion_tokens":        "completion_tokens",
        "total_tokens":             "total_tokens",
        # Anthropic
        "input_tokens":             "prompt_tokens",
        "output_tokens":            "completion_tokens",
        # Google Gemini
        "promptTokenCount":         "prompt_tokens",
        "candidatesTokenCount":     "completion_tokens",
        "totalTokenCount":          "total_tokens",
        # n8n tokenUsageEstimate (camelCase)
        "promptTokens":             "prompt_tokens",
        "completionTokens":         "completion_tokens",
        "totalTokens":              "total_tokens",
    }

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for src_key, dst_key in field_map.items():
            if src_key in candidate and usage[dst_key] is None:
                usage[dst_key] = candidate[src_key]

    # Derive total if missing
    if usage["total_tokens"] is None:
        p = usage["prompt_tokens"] or 0
        c = usage["completion_tokens"] or 0
        if p or c:
            usage["total_tokens"] = p + c

    return usage


def extract_reply_text(response_body: dict) -> str:
    """Pull the human-readable reply out of the n8n response."""
    # Common shapes returned by n8n AI Agent / Chat nodes
    for key in ("output", "text", "message", "reply", "answer", "response", "result", "finalAnswer"):
        val = response_body.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, list) and val:
            first = val[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                for sub in ("text", "output", "message", "content"):
                    if isinstance(first.get(sub), str):
                        return first[sub]
    return "(no text field found in response)"


def send_prompt(webhook_url: str, prompt: str, session_id: str, refOutput: str, ollama_model: str = None) -> dict:
    """
    POST the prompt to the n8n Chat Trigger and return timing + raw body.
    n8n Chat Trigger expects JSON: { "chatInput": "...", "sessionId": "..." }
    """
    payload = {
        "chatInput": prompt,
        "referenceOutput": refOutput , #For correctness evaluation, we need to send the reference output as well
        "sessionId": session_id,
        "ollamaModel": ollama_model,  # Optional field to specify Ollama model for evaluation
    }
    headers = {"Content-Type": "application/json"}

    #t_start = time.perf_counter()
    ts_utc  = datetime.now(timezone.utc).isoformat()

    resp = requests.post(
        webhook_url,
        json=payload,
        headers=headers,
        timeout=None,
    )

    #t_end          = time.perf_counter()
    #latency_ms     = round((t_end - t_start) * 1000, 2)
    #time_to_first  = latency_ms  # single-shot; streaming would differ

    resp.raise_for_status()

    try:
        body = resp.json()
    except ValueError:
        body = {"raw_text": resp.text}

    return {
        "timestamp_utc":   ts_utc,
        "http_status":     resp.status_code,
        "latency_ms":      body.get("latencyMs", None),
        #"time_to_first_ms": time_to_first,
        "response_size_bytes": len(resp.content),
        "body":            body,
    }


# ── output formatters ─────────────────────────────────────────────────────────

def print_table(result: dict) -> None:
    sep = "─" * 52
    print(f"\n{'═' * 52}")
    print(f"  n8n Chat — Response Report")
    print(f"{'═' * 52}")
    print(f"  Timestamp (UTC)   : {result['timestamp_utc']}")
    print(f"  Session ID        : {result['session_id']}")
    print(f"  HTTP Status       : {result['http_status']}")
    print(sep)
    print(f"  ⏱  Latency")
    print(f"     Total          : {result['latency_ms']} ms")
    print(sep)
    print(f"  🔢  Token Usage for Ollama Model: {result.get('ollama_model', 'n/a')}")
    u = result["token_usage"]
    print(f"     Prompt tokens  : {u['prompt_tokens']  or 'n/a'}")
    print(f"     Completion     : {u['completion_tokens'] or 'n/a'}")
    print(f"     Total          : {u['total_tokens']   or 'n/a'}")
    print(sep)
    print(f"  📦  Response size : {result['response_size_bytes']} bytes")
    print(f"{'═' * 52}")
    print(f"\n💬  Reply:\n{result['reply_text']}\n")
    print(f"{'═' * 52}")
    print(f"  🧪  Task Completion Evaluation (if reference output provided) - TraceId = {result.get('TraceId', 'n/a')}")
    print(f"\n Task Completion Score: {result['tc_score']}")
    print(f"\n Reason: {result['tc_reason']}\n")
    print(f"\n MCP Use Score: {result['mcpu_score']}")
    print(f"\n Reason: {result['mcpu_reason']}\n")

def print_json(result: dict) -> None:
    output = {k: v for k, v in result.items() if k != "raw_body"}
    print(json.dumps(output, indent=2, default=str))


def get_csv_row(result: dict):
    u = result["token_usage"]
    headers = [
        "timestamp_utc",
        "session_id",
        "http_status",
        "latency_ms",
        "ollama_model",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "response_size_bytes",
        "tc_score",
        "tc_reason",
        "mcpu_score",
        "mcpu_reason",
        "actual_response",
    ]
    row = [
        result["timestamp_utc"],
        result["session_id"],
        str(result["http_status"]),
        str(result["latency_ms"]),
        str(result.get("ollama_model", "") or ""),
        str(u["prompt_tokens"] or ""),
        str(u["completion_tokens"] or ""),
        str(u["total_tokens"] or ""),
        str(result["response_size_bytes"]),
        str(result.get("tc_score", "") or ""),
        str(result.get("tc_reason", "") or ""),
        str(result.get("mcpu_score", "") or ""),
        str(result.get("mcpu_reason", "") or ""),
        str(result.get("reply_text", "") or ""),
    ]
    return headers, row


def print_csv(result: dict) -> None:
    headers, row = get_csv_row(result)
    writer = csv.writer(sys.stdout)
    writer.writerow(headers)
    writer.writerow(row)


def write_csv_file(result: dict, file_path: str) -> None:
    headers, row = get_csv_row(result)
    file_exists = False
    try:
        file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except OSError:
        file_exists = False

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(row)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    reference_output = """ Here is the requested information:
                               Total UEs with reports: 1
                               Latest Usage Volume (imsi-001010000000001):
                                    Uplink: 5,467 bytes
                                    Downlink: 0 bytes
                                    Total: 5,467 bytes
                                    Timestamp: 2026-04-14T21:30:19.371108+00:00
                                This answer structure should be reapeted for each UE with reports in the requested time range."""
   
    parser = argparse.ArgumentParser(
        description="Submit a prompt to an LangGraph webhook and report latency + token usage + deepEval results."
    )
    parser.add_argument("--url",     required=True,  help="LangGraph webhook URL")
    parser.add_argument("--prompt",  required=True,  help="Prompt to send")
    parser.add_argument("--session", default=None,   help="Session ID (auto-generated if omitted)")
    parser.add_argument("--timeout", type=int, default=None, help="HTTP timeout in seconds (default: none)")
    parser.add_argument("--reference_output", default=reference_output, help="Reference output for correctness evaluation (optional)")
    parser.add_argument("--ollama_model", default=None, help="Specify the Ollama model name for evaluation (optional)")
    parser.add_argument(
        "--output",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--output_file",
        help="Write CSV output to this file (only valid with --output csv)",
    )
    args = parser.parse_args()

    if args.output_file and args.output != "csv":
        parser.error("--output_file may only be used with --output csv")

    session_id = args.session or f"session-{uuid.uuid4().hex[:8]}"

    print(f"🚀  Sending prompt to {args.url} …", file=sys.stderr)

    try:
        raw = send_prompt(args.url, args.prompt, session_id, args.reference_output, args.ollama_model)
        #print(raw)
    except requests.exceptions.Timeout:
        sys.exit(f"❌  Request timed out after {args.timeout}s")
    except requests.exceptions.ConnectionError as e:
        sys.exit(f"❌  Connection error: {e}")
    except requests.exceptions.HTTPError as e:
        sys.exit(f"❌  HTTP error {e.response.status_code}: {e.response.text[:300]}")

    token_usage = extract_token_usage(raw["body"])
    reply_text  = extract_reply_text(raw["body"])

    result = {
        "timestamp_utc":        raw["timestamp_utc"],
        "session_id":           session_id,
        "http_status":          raw["http_status"],
        "latency_ms":           raw["latency_ms"],
        #"time_to_first_ms":     raw["time_to_first_ms"],
        "response_size_bytes":  raw["response_size_bytes"],
        "token_usage":          token_usage,
        "reply_text":           reply_text,
        "raw_body":             raw["body"],
        "ollama_model":         args.ollama_model,
        "tc_score":             raw["body"].get("evaluationResult", None).get("task_completion", None)[0],  # Placeholder for correctness evaluation score
        "tc_reason":            raw["body"].get("evaluationResult", None).get("task_completion", None)[1],  # Placeholder for correctness evaluation reasoning
        "mcpu_score":           raw["body"].get("evaluationResult", None).get("mcp_use", None)[0],  # Placeholder for multi-choice evaluation score
        "mcpu_reason":          raw["body"].get("evaluationResult", None).get("mcp_use", None)[1],  # Placeholder for multi-choice evaluation reasoning
        "TraceId":              raw["body"].get("traceId", None),  # Placeholder for trace ID if available
    }

    if args.output == "table":
        print_table(result)
    elif args.output == "json":
        print_json(result)
    elif args.output == "csv":
        print_csv(result)
        if args.output_file:
            write_csv_file(result, args.output_file)
            print(f"✅  CSV written to {args.output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()