"""Slow loopback HTTP fixture using the production downloader.

Compiles a separate test Main with the real updater source. No alternate URL is
added to the shipped updater's CLI and no TLS/certificate setting is disabled.
"""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import threading
import time

REPO = Path(__file__).resolve().parents[2]
PAYLOAD = bytes(range(256)) * 8192  # 2 MiB, deterministic and anonymous
SHA = hashlib.sha256(PAYLOAD).hexdigest()


class Fixture(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def do_GET(self):
        mode = self.path.strip("/")
        if mode not in ("known", "unknown", "drop-known", "drop-unknown", "eof-unknown"):
            self.send_error(404)
            return
        known = mode in ("known", "drop-known")
        chunked = mode in ("unknown", "drop-unknown")
        self.send_response(200)
        if known:
            self.send_header("Content-Length", str(len(PAYLOAD)))
        elif chunked:
            self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        limit = 786432 if mode.startswith("drop-") or mode == "eof-unknown" else len(PAYLOAD)
        try:
            for pos in range(0, limit, 65536):
                block = PAYLOAD[pos:pos + 65536]
                if chunked:
                    self.wfile.write(f"{len(block):x}\r\n".encode() + block + b"\r\n")
                else:
                    self.wfile.write(block)
                self.wfile.flush()
                time.sleep(0.12)
            if mode.startswith("drop-"):
                # Real mid-response TCP reset, not a synthetic exception in Download.
                self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("hh", 1, 0))
                self.connection.close()
            elif chunked:
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path, help="New evidence directory")
    parser.add_argument("--serve", action="store_true", help="Keep fixture alive for external native PTY checks")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    binary = out / "RuUpdaterDownloadTest.exe"
    compile_result = subprocess.run([
        str(csc), "/nologo", "/optimize+", "/codepage:65001",
        "/r:System.IO.Compression.dll", "/r:System.IO.Compression.FileSystem.dll", "/r:System.Web.Extensions.dll",
        "/main:RuUpdaterDownloadTest", "/out:" + str(binary),
        str(REPO / "scripts/updater/PoB2RUUpdater.cs"), str(REPO / "tests/localization/RuUpdaterDownloadTest.cs")
    ], capture_output=True, encoding="utf-8", errors="replace")
    (out / "compile.log").write_text(compile_result.stdout + compile_result.stderr, encoding="utf-8")
    assert compile_result.returncode == 0, compile_result.stderr
    shutil.copyfile(REPO / "runtime/PoB2RUUpdater.exe.config", str(binary) + ".config")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}/"
    info = {"base": base, "sha256": SHA, "bytes": len(PAYLOAD), "binary": str(binary),
            "fixture_tls_override": False, "production_cli_changed": False}
    (out / "fixture.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    try:
        if args.serve:
            print(json.dumps(info), flush=True)
            deadline = time.monotonic() + 900
            while not (out / "stop.txt").exists() and time.monotonic() < deadline:
                time.sleep(0.2)
            return
        results = {}

        def execute(name, mode, path, expected):
            started = time.monotonic()
            lines, stamps = [], []
            process = subprocess.Popen([str(binary), base + mode, str(path), SHA],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                text=True, encoding="utf-8-sig", errors="replace", bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW)
            for line in process.stdout:
                lines.append(line)
                if line.startswith("Скачано:"):
                    stamps.append({"elapsed": time.monotonic() - started, "text": line.strip()})
            code = process.wait(timeout=45)
            elapsed = time.monotonic() - started
            log = "".join(lines)
            (out / (name + ".log")).write_text(log, encoding="utf-8")
            assert code == expected, log
            assert 1 <= len(stamps) <= math.ceil(elapsed) + 3, "Progress spam or missing progress"
            if mode in ("known", "unknown"):
                assert elapsed >= 3 and len(stamps) >= 3, "Slow fixture did not exercise periodic progress"
                assert hashlib.sha256(path.read_bytes()).hexdigest() == SHA
                assert "FIXTURE_VERIFIED" in log
            else:
                assert "FIXTURE_VERIFIED" not in log
                assert "Причина:" in log and "Ctrl+U" in log and "Загрузка начнётся заново" in log
                assert "Запустите вручную" not in log and "Готово" not in log
                assert 0 < path.stat().st_size < len(PAYLOAD), "Expected an interrupted file"
            if mode in ("unknown", "drop-unknown", "eof-unknown"):
                assert all("%" not in s["text"] and " из " not in s["text"] for s in stamps)
            if mode == "known":
                assert any("100,0%" in s["text"] for s in stamps)
                assert any("%" in s["text"] and "100,0%" not in s["text"] and "(0,0%)" not in s["text"] for s in stamps)
            result = {"exit_code": code, "seconds": elapsed, "progress_updates": len(stamps), "progress": stamps,
                      "file_bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            results[name] = result
            print(name, "PASS", round(elapsed, 2), "seconds,", len(stamps), "updates", flush=True)

        execute("known-clean", "known", out / "known.bin", 0)
        execute("unknown-clean", "unknown", out / "unknown.bin", 0)
        partial = out / "retry.bin"
        execute("drop-known", "drop-known", partial, 1)
        execute("retry-after-known-drop", "known", partial, 0)
        execute("drop-unknown", "drop-unknown", partial, 1)
        execute("retry-after-unknown-drop", "unknown", partial, 0)
        execute("unknown-premature-eof", "eof-unknown", partial, 1)
        # Pre-existing incomplete garbage must be truncated, never resumed/appended.
        partial.write_bytes(b"old interrupted download" * 50000)
        execute("retry-over-existing-partial", "known", partial, 0)
        (out / "result.json").write_text(json.dumps({"passed": True, "cases": results, **info},
            ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
