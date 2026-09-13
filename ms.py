#!/usr/bin/env python3

"""
WebIDE server — single-file, stdlib-only Python backend.

Run on Termux (or any machine) and open the printed URL in a browser
on another device on the same network (e.g. your laptop).

    python server.py --root ~/myprojects --port 8765

Requires only the Python standard library. Git operations require the
`git` binary to be installed (`pkg install git` on Termux).

Design principle: this server never decides anything and never talks
to the AI on its own. Every endpoint here is a dumb, explicit action
triggered by a request the browser only sends when you click a
button. All "AI" traffic is a plain proxy to the Gemini API — the
prompt, the files it can see, and the files it's allowed to touch are
all assembled in the browser, by you, before the request is sent.
"""

import argparse
import json
import mimetypes
import os
import secrets
import shutil
import socket
import subprocess
import sys
import traceback
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

# --------------------------------------------------------------------------
# Config (filled in from CLI args at startup)
# --------------------------------------------------------------------------

ROOT: Path = None    # resolved absolute root directory, all client paths are relative to this
TOKEN: str = None          # shared-secret auth token
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB — files bigger than this refuse to open in the editor
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

HERE = Path(__file__).resolve().parent
INDEX_HTML_PATH = HERE / "ms.html"


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


# --------------------------------------------------------------------------
# Path safety
# --------------------------------------------------------------------------

def safe_path(rel: str) -> Path:
    """Resolve a client-supplied relative path safely under ROOT.

    Raises ApiError if the resolved path would escape ROOT.
    """
    rel = (rel or "").strip().replace("\\", "/")
    if rel in ("", ".", "/"):
        candidate = ROOT
    else:
        candidate = ROOT / rel.lstrip("/")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        raise ApiError(f"path escapes root: {rel}", 403)
    return resolved


def rel_of(p: Path) -> str:
    return str(p.relative_to(ROOT).as_posix()) or "."


# --------------------------------------------------------------------------
# API handlers — each takes parsed input, returns a JSON-serializable dict
# --------------------------------------------------------------------------

def api_health(_qs):
    return {"ok": True, "root": str(ROOT), "time": datetime.now().isoformat(timespec="seconds")}


def api_list(qs):
    rel = (qs.get("path", [""])[0])
    target = safe_path(rel)
    if not target.exists():
        raise ApiError("not found", 404)
    if not target.is_dir():
        raise ApiError("not a directory", 400)
    entries = []
    with os.scandir(target) as it:
        for entry in it:
            try:
                st = entry.stat(follow_symlinks=False)
                entries.append({
                    "name": entry.name,
                    "path": rel_of(Path(entry.path)),
                    "type": "dir" if entry.is_dir(follow_symlinks=False) else "file",
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                })
            except OSError:
                continue
    entries.sort(key=lambda e: (e["type"] != "dir", e["name"].lower()))
    return {"ok": True, "path": rel_of(target), "entries": entries}


def api_file_get(qs):
    rel = qs.get("path", [""])[0]
    target = safe_path(rel)
    if not target.exists() or not target.is_file():
        raise ApiError("file not found", 404)
    size = target.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ApiError(f"file too large to edit here ({size} bytes, limit {MAX_FILE_BYTES})", 413)
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ApiError("binary or non-utf-8 file — cannot open in the text editor", 415)
    return {"ok": True, "path": rel_of(target), "content": content, "lines": content.count("\n") + 1}


def api_file_put(body):
    rel = body.get("path")
    content = body.get("content")
    if rel is None or content is None:
        raise ApiError("path and content are required")
    target = safe_path(rel)
    if target.is_dir():
        raise ApiError("path is a directory", 400)
    if not target.parent.exists():
        raise ApiError("parent directory does not exist", 400)
    data = content.encode("utf-8")
    target.write_bytes(data)
    return {"ok": True, "path": rel_of(target), "bytes": len(data)}


def api_create(body):
    rel = body.get("path")
    kind = body.get("type")
    if not rel or kind not in ("file", "dir"):
        raise ApiError("path and type ('file'|'dir') are required")
    target = safe_path(rel)
    if target.exists():
        raise ApiError("already exists", 409)
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind == "dir":
        target.mkdir()
    else:
        target.touch()
    return {"ok": True, "path": rel_of(target), "type": kind}


def api_move(body):
    items = body.get("items") or []
    dest = body.get("dest", "")
    if not items:
        raise ApiError("items is required")
    dest_path = safe_path(dest)
    dest_is_dir = dest_path.is_dir()
    if len(items) > 1 and not dest_is_dir:
        raise ApiError("moving multiple items requires an existing destination folder")
    moved, errors = [], []
    for item in items:
        try:
            src = safe_path(item)
            if not src.exists():
                raise ApiError("source not found", 404)
            target = (dest_path / src.name) if dest_is_dir else dest_path
            if target.exists():
                raise ApiError(f"destination already exists: {rel_of(target)}", 409)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(target))
            moved.append({"from": item, "to": rel_of(target)})
        except ApiError as e:
            errors.append({"item": item, "error": e.message})
        except Exception as e:
            errors.append({"item": item, "error": str(e)})
    return {"ok": len(errors) == 0, "moved": moved, "errors": errors}


def api_delete(body):
    items = body.get("items") or []
    if not items:
        raise ApiError("items is required")
    deleted, errors = [], []
    for item in items:
        try:
            target = safe_path(item)
            if target == ROOT:
                raise ApiError("refusing to delete the root folder", 403)
            if not target.exists():
                raise ApiError("not found", 404)
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            deleted.append(item)
        except ApiError as e:
            errors.append({"item": item, "error": e.message})
        except Exception as e:
            errors.append({"item": item, "error": str(e)})
    return {"ok": len(errors) == 0, "deleted": deleted, "errors": errors}


def _run_git(args, cwd, timeout):
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, text=True, timeout=timeout,
        )
        return {"cmd": "git " + " ".join(args), "code": proc.returncode,
                "out": proc.stdout.strip(), "err": proc.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"cmd": "git " + " ".join(args), "code": -1, "out": "", "err": "timed out"}


def api_git(body):
    if shutil.which("git") is None:
        raise ApiError("git is not installed on this device (try: pkg install git)", 500)
    rel = body.get("path", "")
    message = (body.get("message") or "").strip()
    if not message:
        message = f"Auto commit — {datetime.now().isoformat(timespec='seconds')}"
    cwd = safe_path(rel)
    if not cwd.is_dir():
        raise ApiError("git folder is not a directory", 400)
    steps = [
        _run_git(["add", "-A"], cwd, 30),
        _run_git(["commit", "-m", message], cwd, 30),
        _run_git(["push"], cwd, 180),
    ]
    ok = all(s["code"] == 0 for s in steps[:1]) and steps[-1]["code"] == 0
    return {"ok": ok, "path": rel_of(cwd), "steps": steps}

def api_gemini(body):
    # Accept either a single 'apiKey' string or an 'apiKeys' list
    raw_keys = body.get("apiKeys") or [body.get("apiKey")]
    api_keys = [k.strip() for k in raw_keys if k and isinstance(k, str) and k.strip()]
    
    model = body.get("model")
    payload = body.get("body")
    
    if not api_keys or not model or not isinstance(payload, dict):
        raise ApiError("apiKeys (or apiKey), model, and body are required")

    data = json.dumps(payload).encode("utf-8")
    last_error = None

    # Try each key sequentially until one succeeds
    for idx, key in enumerate(api_keys):
        url = f"{GEMINI_BASE}/{model}:generateContent?key={key}"
        req = urllib.request.Request(
            url, 
            data=data, 
            method="POST",
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
                return {"ok": True, "data": json.loads(raw), "key_index_used": idx}
                
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw
            
            last_error = f"HTTP {e.code}: {parsed}"
            
            # Key exhausted (429 Rate Limit, 403 Forbidden/Quota) -> continue to next key
            if e.code in (429, 403, 400):
                continue 
            else:
                # Non-key related HTTP error (e.g., 500 internal server error)
                raise ApiError(f"Gemini API error: {last_error}", 502)
                
        except urllib.error.URLError as e:
            raise ApiError(f"Could not reach Gemini API: {e.reason}", 502)

    # If the loop finishes, all keys failed
    raise ApiError(f"All provided API keys were exhausted or rejected. Last error: {last_error}", 429)

# --------------------------------------------------------------------------
# HTTP plumbing
# --------------------------------------------------------------------------

GET_ROUTES = {
    "/api/health": api_health,
    "/api/list": api_list,
    "/api/file": api_file_get,
}
POST_ROUTES = {
    "/api/file": api_file_put,
    "/api/create": api_create,
    "/api/move": api_move,
    "/api/delete": api_delete,
    "/api/git": api_git,
    "/api/gemini": api_gemini,
}


class Handler(BaseHTTPRequestHandler):
    server_version = "WebIDE/1.0"
    protocol_version = "HTTP/1.1"

    def _send_json(self, obj, status=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except BrokenPipeError:
            pass

    def _authorized(self):
        got = self.headers.get("X-Auth-Token", "")
        return secrets.compare_digest(got, TOKEN)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            raise ApiError("invalid JSON body")

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def do_GET(self):
        parts = urlsplit(self.path)
        if parts.path == "/" or parts.path == "/index.html":
            self._serve_index()
            return
        if parts.path.startswith("/api/"):
            if not self._authorized():
                self._send_json({"ok": False, "error": "unauthorized"}, 401)
                return
            handler = GET_ROUTES.get(parts.path)
            if not handler:
                self._send_json({"ok": False, "error": "unknown endpoint"}, 404)
                return
            qs = parse_qs(parts.query)
            try:
                self._send_json(handler(qs))
            except ApiError as e:
                self._send_json({"ok": False, "error": e.message}, e.status)
            except Exception:
                traceback.print_exc()
                self._send_json({"ok": False, "error": "internal error"}, 500)
            return
        self._send_json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        parts = urlsplit(self.path)
        if not parts.path.startswith("/api/"):
            self._send_json({"ok": False, "error": "not found"}, 404)
            return
        if not self._authorized():
            # still need to drain the body so the connection stays usable
            length = int(self.headers.get("Content-Length", 0) or 0)
            if length:
                self.rfile.read(length)
            self._send_json({"ok": False, "error": "unauthorized"}, 401)
            return
        handler = POST_ROUTES.get(parts.path)
        if not handler:
            self._send_json({"ok": False, "error": "unknown endpoint"}, 404)
            return
        try:
            body = self._read_json_body()
            self._send_json(handler(body))
        except ApiError as e:
            self._send_json({"ok": False, "error": e.message}, e.status)
        except Exception:
            traceback.print_exc()
            self._send_json({"ok": False, "error": "internal error"}, 500)

    def _serve_index(self):
        try:
            data = INDEX_HTML_PATH.read_bytes()
        except FileNotFoundError:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"index.html not found next to server.py")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


# --------------------------------------------------------------------------
# Startup
# --------------------------------------------------------------------------

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    global ROOT, TOKEN
    parser = argparse.ArgumentParser(description="WebIDE server")
    parser.add_argument("--root", default="~/ms-dos/projects", help="folder to browse/edit (default: current directory)")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="port (default: 8001)")
    parser.add_argument("--token", default=None, help="fixed auth token (default: random, printed on start)")
    args = parser.parse_args()

    ROOT = Path(args.root).expanduser().resolve()
    if not ROOT.is_dir():
        print(f"error: --root {ROOT} is not a directory", file=sys.stderr)
        sys.exit(1)
    TOKEN = "373737"

    mimetypes.init()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True

    lan_ip = get_lan_ip()
    print("=" * 60)
    print(" WebIDE server is running")
    print(f"   Root:    {ROOT}")
    print(f"   Local:   http://127.0.0.1:{args.port}/")
    print(f"   Network: http://{lan_ip}:{args.port}/   <-- other device")
    print(f"   Token:   {TOKEN}")
    print("   (paste the token into the app's Settings panel on first load)")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.shutdown()


if __name__ == "__main__":
    main()

