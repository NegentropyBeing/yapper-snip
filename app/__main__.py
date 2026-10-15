"""Launcher: python -m app [run|stop|restart|purge-cache|purge-models]."""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

from . import clips, models
from .config import HOST, PORT
from .lifecycle import EXIT_RESTART, SUPERVISED_ENV


def is_up(url: str) -> bool:
    """True when yapper-snip itself, not some other program, answers on url."""
    try:
        with urllib.request.urlopen(f"{url}/api/capabilities", timeout=2) as response:
            return "isolate_steps" in json.load(response)
    except (OSError, ValueError):
        return False


def open_when_up(url: str) -> None:
    for _ in range(120):
        if is_up(url):
            webbrowser.open(url)
            return
        time.sleep(0.5)


def serve(host: str, port: int, open_browser: bool = False) -> int:
    """Run the server, starting it again whenever it asks for a restart."""
    url = f"http://{host}:{port}"
    if open_browser:
        if is_up(url):
            print(f"yapper-snip is already running: {url}")
            webbrowser.open(url)
            return 0
        threading.Thread(target=open_when_up, args=(url,), daemon=True).start()
    env = dict(os.environ, **{SUPERVISED_ENV: "1"})
    command = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    print(f"yapper-snip: {url}")
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


PURGE = {"purge-cache": clips.purge, "purge-models": models.purge}


def megabytes(result: dict) -> str:
    return f"{result['freed_bytes'] / 1e6:.1f} MB freed"


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app", description="yapper-snip launcher")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "stop", "restart", *PURGE])
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--open", action="store_true", help="with run: open the page in the default browser")
    args = parser.parse_args()

    if args.command == "run":
        return serve(args.host, args.port, args.open)

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
