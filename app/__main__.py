"""Launcher: python -m app [run|stop|restart|purge-cache|purge-models]."""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

from . import clips, isolate
from .config import EXIT_RESTART, HOST, PORT


def serve(host: str, port: int) -> int:
    """Run the server, starting it again whenever it asks for a restart."""
    env = dict(os.environ, YAPPER_SUPERVISED="1")
    command = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    print(f"yapper-snip: http://{host}:{port}")
    while True:
        try:
            code = subprocess.call(command, env=env)
        except KeyboardInterrupt:
            return 0
        if code != EXIT_RESTART:
            return code
        print("yapper-snip: restarting")


def call(host: str, port: int, action: str) -> dict:
    request = urllib.request.Request(
        f"http://{host}:{port}/api/admin/{action}",
        data=b"{}",
        headers={"Content-Type": "application/json", "X-Yapper": "1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise SystemExit(json.load(exc).get("detail", str(exc)))


PURGE = {"purge-cache": clips.purge, "purge-models": isolate.purge_models}


def megabytes(result: dict) -> str:
    return f"{result['freed_bytes'] / 1e6:.1f} MB freed"


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app", description="yapper-snip launcher")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "stop", "restart", *PURGE])
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    if args.command == "run":
        return serve(args.host, args.port)

    try:
        if args.command in PURGE:
            print(megabytes(call(args.host, args.port, args.command)))
        else:
            call(args.host, args.port, args.command)
            print("Stopping" if args.command == "stop" else "Restarting")
    except urllib.error.URLError:
        if args.command not in PURGE:
            print(f"No app is running on {args.host}:{args.port}")
            return 1
        # Nothing is running, so the folder can be cleared straight from disk.
        print(megabytes(PURGE[args.command]()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
