import http.server
import json
import os
import shutil
import subprocess
import re

BASE_DIR = os.path.expanduser("~/ms-dos/dos")

def ensure_dir():
    os.makedirs(BASE_DIR, exist_ok=True)

def validate_name(name):
    clean = name.strip().lower()
    if not re.match(r'^[a-z0-9_\-]+$', clean):
        raise ValueError("Invalid name: Only lowercase letters, numbers, underscores, and hyphens are allowed.")
    return clean

def sync_dos_to_github(commit_message="Auto-sync: update dos data"):
    if not os.path.isdir(BASE_DIR):
        raise Exception("DOS directory does not exist.")
    if not os.path.isdir(os.path.join(BASE_DIR, ".git")):
        try:
            subprocess.run(["git", "init"], cwd=BASE_DIR, check=True)
        except Exception as e:
            raise Exception(f"Git init failed: {e}")
    try:
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=BASE_DIR, capture_output=True, text=True, check=True)
        if not status.stdout.strip():
            return True
        subprocess.run(["git", "commit", "-m", commit_message], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "push"], cwd=BASE_DIR, check=True)
        return True
    except subprocess.CalledProcessError as e:
        raise Exception(f"Git sync failed: {e}")

def parse_filename(filename):
    base = os.path.splitext(filename)[0]
    if len(base) >= 2 and base[0].isdigit() and base[1].isdigit():
        status = int(base[0])
        second = int(base[1])
        label = base[3:] if len(base) > 2 and base[2] == '_' else base[2:]
        return status, second, label
    return 3, 2, base

def build_tree(current_path, node_id="root", label="dos"):
    ensure_dir()
    if not os.path.exists(current_path):
        os.makedirs(current_path, exist_ok=True)
        
    ds_content = ""
    ds_path = os.path.join(current_path, "ds.txt")
    if os.path.exists(ds_path) and os.path.isfile(ds_path):
        try:
            with open(ds_path, "r", encoding="utf-8") as f:
                ds_content = f.read()
        except Exception:
            ds_content = ""

    children = []
    try:
        entries = sorted(os.listdir(current_path))
    except Exception:
        entries = []

    for entry in entries:
        if entry.startswith('.'):
            continue
        if entry == "ds.txt":
            continue
        full_path = os.path.join(current_path, entry)
        if os.path.isdir(full_path):
            status, second, clean_label = parse_filename(entry)
            child_node = build_tree(full_path, node_id=entry, label=clean_label)
            child_node["kind"] = "folder"
            child_node["status"] = status
            child_node["second"] = second
            children.append(child_node)
        elif os.path.isfile(full_path) and not entry.endswith('.meta.json'):
            status, second, clean_label = parse_filename(entry)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                content = ""
            children.append({
                "id": entry,
                "kind": "problem",
                "label": clean_label,
                "status": status,
                "second": second,
                "content": content
            })

    return {
        "id": node_id,
        "kind": "folder",
        "label": label,
        "ds_content": ds_content,
        "children": children
    }

def get_dir_from_path(path_list):
    curr = BASE_DIR
    for segment in path_list:
        matched = None
        if os.path.exists(curr):
            for entry in os.listdir(curr):
                if os.path.isdir(os.path.join(curr, entry)):
                    _, _, lbl = parse_filename(entry)
                    if lbl == segment:
                        matched = entry
                        break
        if matched:
            curr = os.path.join(curr, matched)
        else:
            curr = os.path.join(curr, f"32_{segment}")
    return curr

def get_entry_path(path_arr):
    if not path_arr:
        return BASE_DIR
    parent_arr = path_arr[:-1]
    target_name = path_arr[-1]
    parent_dir = get_dir_from_path(parent_arr)
    if os.path.exists(parent_dir):
        for entry in os.listdir(parent_dir):
            if entry == "ds.txt":
                continue
            _, _, lbl = parse_filename(entry)
            if lbl == target_name:
                return os.path.join(parent_dir, entry)
    return os.path.join(parent_dir, f"32_{target_name}")

class DOSHandler(http.server.SimpleHTTPRequestHandler):
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path == "/api/tree":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            tree = build_tree(BASE_DIR)
            self.wfile.write(json.dumps(tree).encode("utf-8"))
        else:
            if self.path == "/" or self.path == "":
                self.path = "./ms-dos/dos.html"
            return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            data = {}

        ensure_dir()
        response = {"success": True}
        
        try:
            if self.path == "/api/node/create":
                parent_path = data.get("parentPath", [])
                kind = data.get("kind")
                name = validate_name(data.get("name", ""))
                status = data.get("status", 3)
                second = data.get("second", 2)
                
                target_dir = get_dir_from_path(parent_path)
                os.makedirs(target_dir, exist_ok=True)
                
                filename = f"{status}{second}_{name}"
                if kind == "folder":
                    os.makedirs(os.path.join(target_dir, filename), exist_ok=True)
                else:
                    open(os.path.join(target_dir, filename), "w", encoding="utf-8").close()
                    
            elif self.path == "/api/folder/ds":
                path_arr = data.get("path", [])
                content = data.get("content", "")
                target_dir = get_dir_from_path(path_arr)
                os.makedirs(target_dir, exist_ok=True)
                ds_path = os.path.join(target_dir, "ds.txt")
                with open(ds_path, "w", encoding="utf-8") as f:
                    f.write(content)

            elif self.path == "/api/node/renumber":
                path_arr = data.get("path", [])
                status = data.get("status")
                second = data.get("second")
                
                if path_arr:
                    parent_path_arr = path_arr[:-1]
                    old_name = path_arr[-1]
                    target_dir = get_dir_from_path(parent_path_arr)
                    if os.path.exists(target_dir):
                        for entry in os.listdir(target_dir):
                            if entry == "ds.txt":
                                continue
                            _, _, lbl = parse_filename(entry)
                            if lbl == old_name:
                                old_full = os.path.join(target_dir, entry)
                                new_filename = f"{status}{second}_{old_name}"
                                new_full = os.path.join(target_dir, new_filename)
                                os.rename(old_full, new_full)
                                break
                            
            elif self.path == "/api/node/delete":
                path_arr = data.get("path", [])
                if path_arr:
                    parent_path_arr = path_arr[:-1]
                    target_name = path_arr[-1]
                    target_dir = get_dir_from_path(parent_path_arr)
                    if os.path.exists(target_dir):
                        for entry in os.listdir(target_dir):
                            if entry == "ds.txt":
                                continue
                            _, _, lbl = parse_filename(entry)
                            if lbl == target_name:
                                full_path = os.path.join(target_dir, entry)
                                if os.path.isdir(full_path):
                                    shutil.rmtree(full_path)
                                else:
                                    os.remove(full_path)
                                break
                            
            elif self.path == "/api/node/content":
                path_arr = data.get("path", [])
                content = data.get("content", "")
                if path_arr:
                    parent_path_arr = path_arr[:-1]
                    target_name = path_arr[-1]
                    target_dir = get_dir_from_path(parent_path_arr)
                    if os.path.exists(target_dir):
                        for entry in os.listdir(target_dir):
                            if entry == "ds.txt":
                                continue
                            _, _, lbl = parse_filename(entry)
                            if lbl == target_name and os.path.isfile(os.path.join(target_dir, entry)):
                                with open(os.path.join(target_dir, entry), "w", encoding="utf-8") as f:
                                    f.write(content)
                                break

            elif self.path == "/api/node/rename":
                path_arr = data.get("path", [])
                new_name = validate_name(data.get("newName", ""))
                if path_arr and new_name:
                    parent_path_arr = path_arr[:-1]
                    old_name = path_arr[-1]
                    target_dir = get_dir_from_path(parent_path_arr)
                    if os.path.exists(target_dir):
                        for entry in os.listdir(target_dir):
                            if entry == "ds.txt":
                                continue
                            status, second, lbl = parse_filename(entry)
                            if lbl == old_name:
                                old_full = os.path.join(target_dir, entry)
                                new_filename = f"{status}{second}_{new_name}"
                                new_full = os.path.join(target_dir, new_filename)
                                os.rename(old_full, new_full)
                                break

            elif self.path == "/api/node/move-batch":
                sources = data.get("sources", []) # list of path arrays
                dest_parent_path = data.get("destParentPath", [])
                dest_dir = get_dir_from_path(dest_parent_path)
                os.makedirs(dest_dir, exist_ok=True)
                for src_path in sources:
                    if src_path:
                        src_full = get_entry_path(src_path)
                        if os.path.exists(src_full):
                            basename = os.path.basename(src_full)
                            dest_full = os.path.join(dest_dir, basename)
                            if src_full != dest_full:
                                shutil.move(src_full, dest_full)

            elif self.path == "/api/node/dos/save":
                sync_dos_to_github()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

if __name__ == "__main__":
    port = 8000
    ensure_dir()
    print(f"DOS Server running at http://localhost:{port} -> syncing with {BASE_DIR}")
    http.server.HTTPServer(("0.0.0.0", port), DOSHandler).serve_forever()

