import os, shutil, threading, time, stat, tempfile
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi.responses import StreamingResponse, PlainTextResponse, FileResponse
from typing import List


import docker
from fastapi import FastAPI, HTTPException,BackgroundTasks
from pydantic import BaseModel, Field

# ───── Settings ───────────────────────────────────────────────────
PREVIEW_DOMAIN  = os.getenv("PREVIEW_DOMAIN",  "chat.labyai.app")  # path-based default
PREVIEW_SCHEME  = os.getenv("PREVIEW_SCHEME",  "https")             # "http" for local
ENTRYPOINT_NAME = os.getenv("ENTRYPOINT_NAME", "https")             # "http" for local
DOCKER_NETWORK  = os.getenv("DOCKER_NETWORK",  "shared-network")
RUNNER_IMAGE    = os.getenv("RUNNER_IMAGE",    "labyai/streamlit-runner:latest")

# New: routing mode + base path
ROUTING_MODE    = os.getenv("ROUTING_MODE", "path")                 # "path" | "subdomain"
PATH_PREFIX     = os.getenv("PATH_PREFIX", "/p").rstrip("/")        # e.g. /p

DEFAULT_TTL_MIN = int(os.getenv("DEFAULT_TTL_MIN", "45"))
MAX_LIVE_CONTAINERS = int(os.getenv("MAX_LIVE_CONTAINERS", "50"))
CPU_LIMIT       = os.getenv("CPU_LIMIT", "1")
MEM_LIMIT       = os.getenv("MEM_LIMIT", "1g")
CACHE_VOLUME    = os.getenv("CACHE_VOLUME", "wheels-cache")
SESSIONS_ROOT   = os.getenv("SESSIONS_ROOT", "/var/lib/labyai/sessions")

# ───── Models ─────────────────────────────────────────────────────
class FileItem(BaseModel):
    path: str
    content: str

class LaunchReq(BaseModel):
    files:        Optional[List[FileItem]] = None
    entrypoint:   Optional[str]            = "app.py"
    code:         Optional[str]            = None
    requirements: Optional[str]            = None
    ttl_minutes:  Optional[int]            = None
    bundle_hash:  Optional[str]            = None

class KillReq(BaseModel):
    id: str

# ───── FastAPI & Docker ───────────────────────────────────────────
app    = FastAPI()
client = docker.from_env()
os.makedirs(SESSIONS_ROOT, exist_ok=True)

_now = lambda: datetime.now(timezone.utc)

def _ensure_cache_volume():
    if CACHE_VOLUME not in {v.name for v in client.volumes.list()}:
        client.volumes.create(name=CACHE_VOLUME)

def _safe_write(base: str, rel: str, content: str):
    if rel.startswith("/") or ".." in rel.split("/"):
        raise HTTPException(status_code=400, detail="Bad path")
    tgt = os.path.join(base, rel.replace("\\", "/"))
    os.makedirs(os.path.dirname(tgt), exist_ok=True)
    with open(tgt, "w", encoding="utf-8") as f:
        f.write(content)

def _nano_cpus(v):
    return int(float(v) * 1e9)

def _sid(n=6):
    import secrets
    return secrets.token_hex(n)

# ───── API ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"ok": True}
MAX_BUNDLE_BYTES = int(os.getenv("MAX_BUNDLE_BYTES", 5 * 1024 * 1024))  # 5 MB

def _bundle_too_big(files: List[FileItem]) -> bool:
    total = sum(len(f.content.encode("utf-8")) for f in files)
    return total > MAX_BUNDLE_BYTES

@app.post("/launch")
def launch(req: LaunchReq):
    sid = _sid()
    if req.bundle_hash:
        matches = client.containers.list(
            all=True,
            filters={"label": f"labyai.bundle_hash={req.bundle_hash}"}
        )
        if matches:
            c = matches[0]
            return {
                "id":         c.labels.get("labyai.preview.id"),
                "url":        c.labels.get("labyai.preview.url"),
                "entrypoint": c.labels.get("labyai.preview.entrypoint"),
            }
    ttl = int(req.ttl_minutes or DEFAULT_TTL_MIN)

    # host session dir (one per preview)
    session_dir = os.path.join(SESSIONS_ROOT, sid)
    os.makedirs(session_dir, exist_ok=True)

    if req.files and _bundle_too_big(req.files):
        raise HTTPException(
            status_code=413,
            detail=f"Bundle > {MAX_BUNDLE_BYTES // 1024} KB. "
                   "Split it or raise MAX_BUNDLE_BYTES."
        )
    # write code files
    if req.files:
        for f in req.files:
            _safe_write(session_dir, f.path, f.content)
        entrypoint = (req.entrypoint or "app.py").strip() or "app.py"
    else:
        code = req.code or "import streamlit as st\nst.title('Empty app')\n"
        _safe_write(session_dir, "app.py", code)
        entrypoint = "app.py"

    _safe_write(session_dir, "requirements.txt", (req.requirements or "streamlit\n").strip() + "\n")

    _ensure_cache_volume()

    # make the directory world-writable so non-root runner can write
    os.chmod(session_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0o777

    # ── Build Traefik labels depending on routing mode ────────────
    labels = {"traefik.enable": "true"}
    extra_env = {}

    if ROUTING_MODE.lower() == "path":
        host = PREVIEW_DOMAIN                               # chat.labyai.app
        base_path = f"{PATH_PREFIX}/{sid}"                  # /p/<id>
        rule = f"Host(`{host}`) && PathPrefix(`{base_path}`)"
        labels.update({
            f"traefik.http.routers.{sid}.rule": rule,
            f"traefik.http.routers.{sid}.entrypoints": ENTRYPOINT_NAME,
            f"traefik.http.routers.{sid}.priority": "1000",   # ensure this wins
            f"traefik.http.services.{sid}.loadbalancer.server.port": "8501",
            "labyai.preview": "true",
            "labyai.preview.id": sid,
            "labyai.preview.url": f"{PREVIEW_SCHEME}://{host}{base_path}/",
            "labyai.preview.created_at": _now().isoformat(),
            "labyai.preview.ttl_min": str(ttl),
            "labyai.preview.entrypoint": entrypoint,
            "labyai.bundle_hash": req.bundle_hash or "",
        })
        if PREVIEW_SCHEME == "https":
            labels[f"traefik.http.routers.{sid}.tls"] = "true"
        preview_url = f"{PREVIEW_SCHEME}://{host}{base_path}/"
        extra_env = {"BASE_PATH": base_path,
                      "ENTRYPOINT": f"/session/{entrypoint}"}

    else:
        host = f"{sid}.{PREVIEW_DOMAIN}"
        rule = f"Host(`{host}`)"
        labels.update({
            f"traefik.http.routers.{sid}.rule": rule,
            f"traefik.http.routers.{sid}.entrypoints": ENTRYPOINT_NAME,
            f"traefik.http.services.{sid}.loadbalancer.server.port": "8501",
            "labyai.preview": "true",
            "labyai.preview.id": sid,
            "labyai.preview.url": f"{PREVIEW_SCHEME}://{host}/",
            "labyai.preview.created_at": _now().isoformat(),
            "labyai.preview.ttl_min": str(ttl),
            "labyai.preview.entrypoint": entrypoint,
            "labyai.bundle_hash": req.bundle_hash or "",
        })
        if PREVIEW_SCHEME == "https":
            labels[f"traefik.http.routers.{sid}.tls"] = "true"
        preview_url = f"{PREVIEW_SCHEME}://{host}/"
        extra_env = {
        # NEW – even if there’s no BASE_PATH, still pass ENTRYPOINT
        "ENTRYPOINT": f"/session/{entrypoint}",
    }

    try:
        client.containers.run(
            RUNNER_IMAGE,
            name=f"st-{sid}",
            detach=True,
            mem_limit=MEM_LIMIT,
            nano_cpus=_nano_cpus(CPU_LIMIT),
            read_only=True,
            tmpfs={"/tmp": "rw,noexec,nosuid,size=200m"},
            security_opt=["no-new-privileges"],
            network=DOCKER_NETWORK,
            labels=labels,
            environment=extra_env,   # pass BASE_PATH in path mode
            volumes={
                session_dir:  {"bind": "/session",      "mode": "rw"},
                CACHE_VOLUME: {"bind": "/wheels-cache", "mode": "rw"},
            },
        )
    except docker.errors.ImageNotFound:
        raise HTTPException(status_code=500, detail="Runner image missing")
    except Exception as e:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

    return {"id": sid, "url": preview_url, "entrypoint": entrypoint}

@app.get("/zip/{id}", response_class=FileResponse)
def download_zip(id: str, bg: BackgroundTasks):
    session_dir = os.path.join(SESSIONS_ROOT, id)
    if not os.path.isdir(session_dir):
        raise HTTPException(status_code=404, detail="preview not found")

    # build the archive in /tmp
    tmp = tempfile.NamedTemporaryFile(prefix=f"{id}_", suffix=".zip", delete=False)
    archive_path = shutil.make_archive(tmp.name[:-4], "zip", session_dir)

    # schedule its removal after the response is sent
    bg.add_task(os.unlink, archive_path)

    return FileResponse(
        archive_path,
        filename=f"{id}.zip",
        media_type="application/zip",
    )


@app.post("/kill")
def kill(req: KillReq):
    try:
        client.containers.get(f"st-{req.id}").remove(force=True)
    except docker.errors.NotFound:
        pass
    shutil.rmtree(os.path.join(SESSIONS_ROOT, req.id), ignore_errors=True)
    return {"ok": True}

@app.get("/status/{id}")
def status(id: str):
    name = f"st-{id}"
    try:
        c = client.containers.get(name)
    except docker.errors.NotFound:
        return {"exists": False, "status": "not_found"}
    s = c.attrs or {}
    return {
        "exists": True,
        "status": c.status,  # created | running | exited
        "started_at": s.get("State", {}).get("StartedAt"),
        "finished_at": s.get("State", {}).get("FinishedAt"),
        "labels": c.labels or {},
    }

@app.get("/logs/{id}", response_class=PlainTextResponse)
def logs_tail(id: str, tail: int = 200):
    name = f"st-{id}"
    try:
        c = client.containers.get(name)
    except docker.errors.NotFound:
        return PlainTextResponse("not found", status_code=404)
    out = c.logs(tail=max(1, min(tail, 2000)))
    return out.decode("utf-8", errors="ignore")

@app.get("/logs/{id}/stream")
def logs_stream(id: str):
    name = f"st-{id}"
    try:
        c = client.containers.get(name)
    except docker.errors.NotFound:
        return PlainTextResponse("not found", status_code=404)

    def _iter():
        # include recent context, then follow
        for b in c.logs(stream=True, follow=True, tail=50):
            yield b

    return StreamingResponse(_iter(), media_type="text/plain")

# ───── Sweeper ──────────────────────────────────────────────────
def sweeper_loop():
    while True:
        try:
            # list all previews (running or exited)
            previews = client.containers.list(
                all=True, filters={"label": "labyai.preview=true"}
            )

            # ── TTL cleanup (existing logic) ────────────────────────
            for c in previews:
                lbl = c.labels or {}
                sid = lbl.get("labyai.preview.id")
                created_at = lbl.get("labyai.preview.created_at")
                ttl_min = int(lbl.get("labyai.preview.ttl_min", DEFAULT_TTL_MIN))
                if not (sid and created_at):
                    continue
                try:
                    born = datetime.fromisoformat(created_at)
                except ValueError:
                    continue
                if _now() > born + timedelta(minutes=ttl_min):
                    try:
                        c.remove(force=True)
                    except Exception:
                        pass
                    shutil.rmtree(os.path.join(SESSIONS_ROOT, sid), ignore_errors=True)

            # ── Global cap: remove oldest until <= MAX_LIVE_CONTAINERS ─
            live = client.containers.list(
                all=True, filters={"label": "labyai.preview=true"}
            )
            if len(live) > MAX_LIVE_CONTAINERS:
                # sort by creation time (oldest first)
                live.sort(key=lambda x: x.labels.get("labyai.preview.created_at", ""))
                for c in live[: len(live) - MAX_LIVE_CONTAINERS]:
                    sid = c.labels.get("labyai.preview.id")
                    try:
                        c.remove(force=True)
                    except Exception:
                        pass
                    if sid:
                        shutil.rmtree(os.path.join(SESSIONS_ROOT, sid), ignore_errors=True)

        except Exception:
            pass

        time.sleep(30)

threading.Thread(target=sweeper_loop, daemon=True).start()
