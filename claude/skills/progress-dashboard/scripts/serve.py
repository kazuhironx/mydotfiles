#!/usr/bin/env python3
"""One HTTP hub for every registered project's dashboard.

Routes: `/` lists all projects, `/p/<slug>/` serves that project's dashboard.html.
Nothing else is served: JSON, logs and arbitrary paths stay private, and slugs are
resolved only through the registry, never through the filesystem.
"""

import argparse
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import agents  # noqa: E402
import progress  # noqa: E402
import render  # noqa: E402

BIND_RETRY_SEC = 30
BACK_LINK = '<p class="back"><a href="/">← 全プロジェクト</a> · <a href="/help">使い方</a></p>'


def live_projects():
    """Registered projects whose status.json still exists (removed repos drop out)."""
    out = []
    for p in progress.load_registry()["projects"]:
        root = Path(p.get("root", ""))
        if not (root / progress.DATA_DIR / "status.json").is_file():
            continue
        entry = {"slug": p["slug"], "root": str(root)}
        try:
            entry["status"], entry["decisions"] = progress.view(
                root, progress.load_status(root), progress.load_decisions(root))
        except Exception as e:  # noqa: BLE001
            entry["error"] = str(e)
        out.append(entry)
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "progress-dashboard"
    host_label = ""
    lan_urls = ()

    def do_HEAD(self):
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/", "/index.html"):
                return self.send_html(render.render_index(live_projects(), self.host_label,
                                                          agents.list_agents()), head_only)
            if path in ("/help", "/help/"):
                return self.send_html(render.render_help(self.host_label, self.lan_urls), head_only)
            parts = path.strip("/").split("/")
            if len(parts) == 2 and parts[0] == "p" and path.endswith("/"):
                return self.send_project(parts[1], head_only)
            if len(parts) == 2 and parts[0] == "p":
                self.send_response(301)
                self.send_header("Location", path + "/")
                self.end_headers()
                return None
        except Exception as e:  # noqa: BLE001
            self.log_error("handler failed: %r", e)
            return self.send_error(500)
        return self.send_error(404)

    def send_project(self, slug, head_only):
        match = next((p for p in progress.load_registry()["projects"] if p.get("slug") == slug), None)
        if match is None:
            return self.send_error(404)
        root = Path(match["root"])
        page = root / progress.DATA_DIR / "dashboard.html"
        if progress.html_is_stale(root):
            # The source (e.g. notes/remaining.md) can change by git pull with no session running.
            try:
                with progress.locked(root, wait=0.5):
                    progress.render(root)
            except Exception as e:  # noqa: BLE001
                self.log_error("re-render of %s failed: %r", root, e)
        try:
            text = page.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self.send_error(404)
        text = text.replace("<main>", "<main>" + BACK_LINK, 1)
        return self.send_html(text, head_only)

    def send_html(self, text, head_only):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)
        return None


def serve_forever_on(addr, port, handler):
    """Loopback must come up even if the LAN address is not configured yet."""
    while True:
        try:
            httpd = ThreadingHTTPServer((addr, port), handler)
        except OSError as e:
            print(f"bind {addr}:{port} failed ({e}); retry in {BIND_RETRY_SEC}s", file=sys.stderr, flush=True)
            time.sleep(BIND_RETRY_SEC)
            continue
        print(f"serving http://{addr}:{port}/", file=sys.stderr, flush=True)
        httpd.serve_forever()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bind", action="append", required=True,
                    help="address to listen on (repeatable); avoid 0.0.0.0 on multi-homed hosts")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args(argv)
    Handler.host_label = f"{socket.gethostname()}:{args.port}"
    Handler.lan_urls = tuple(f"http://{a}:{args.port}/" for a in args.bind
                             if not a.startswith("127.") and a != "::1")
    threads = [threading.Thread(target=serve_forever_on, args=(a, args.port, Handler), daemon=True)
               for a in args.bind]
    for t in threads:
        t.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
