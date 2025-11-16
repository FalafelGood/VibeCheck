"""
This module queries a llama model served by ollama on a local host
"""

#!/usr/bin/env python3
import requests
import json
import sys

prompt = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
if not prompt:
    print("Error: No prompt provided", file=sys.stderr)
    sys.exit(1)

url = "http://192.168.0.28:11434/api/generate"

try:
    response = requests.post(url, json={"model": "llama3:8b-instruct-q5_K_M", "prompt": prompt, "stream": True}, stream=True, timeout=30)
    response.raise_for_status()
    
    for line in response.iter_lines(decode_unicode=True):
        if line:
            try:
                data = json.loads(line)
                print(data.get("response", ""), end="", flush=True)
                if data.get("done"):
                    break
            except json.JSONDecodeError:
                continue
    print()
except requests.exceptions.Timeout:
    print("\nError: Request timed out", file=sys.stderr)
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)