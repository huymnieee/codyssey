"""로컬 연습용 서버. Vercel에서는 api/learn.py를 직접 실행합니다."""
import argparse
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from api.learn import handler

ROOT = Path(__file__).resolve().parent


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                name, value = line.split("=", 1)
                if name.strip() in ("GEMINI_API_KEY", "GEMINI_MODEL"):
                    os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


class LocalHandler(SimpleHTTPRequestHandler):
    respond = handler.respond

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if urlsplit(self.path).path == "/api/learn":
            handler.do_POST(self)
        else:
            self.send_error(404)

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/api/learn":
            handler.do_GET(self)
            return
        # 비밀 파일과 소스는 로컬 웹에서도 내려받을 수 없게 합니다.
        if path not in ("/", "/index.html") and not (
            any(path.startswith(prefix) for prefix in ("/css/", "/js/", "/images/")) and
            ".." not in path and not any(part.startswith(".") for part in path.split("/") if part)
        ):
            self.send_error(404)
            return
        if path.endswith("/") and path != "/":
            self.send_error(404)
            return
        super().do_GET()

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8003)
    args = parser.parse_args()
    load_env()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), LocalHandler)
    print(f"공부한입 실행 중: http://127.0.0.1:{args.port}", flush=True)
    print("종료하려면 Ctrl+C를 누르세요.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
