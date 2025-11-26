#!/usr/bin/env python3
import sys
import subprocess
import json
import os

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No shortcode provided"}))
        sys.exit(1)

    shortcode = sys.argv[1]

    # Make sure it has the leading '-' so Instaloader treats it as a post shortcode
    if not shortcode.startswith("-"):
        shortcode = "-" + shortcode

    out_dir = os.path.abspath(f"./insta_{shortcode}")
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        sys.executable,
        "-m", "instaloader",
        "--dirname-pattern", out_dir,
        "--", shortcode
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    payload = {
        "shortcode": shortcode,
        "out_dir": out_dir,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

    print(json.dumps(payload))

if __name__ == "__main__":
    main()