"""Desktop launcher used by the Windows installer.

The installed application starts MiND on localhost, opens the real web interface,
and keeps a small control window available to reopen or stop the local service.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

HOST = "127.0.0.1"
PREFERRED_PORT = 8000
STARTUP_TIMEOUT_SECONDS = 20.0


def ensure_hidden_standard_streams() -> None:
    """Give windowed dependencies safe streams without opening a console."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


ensure_hidden_standard_streams()


def write_smoke_report(message: str) -> None:
    """Write CI-only diagnostics without showing a console to end users."""
    report_path = os.getenv("MIND_SMOKE_REPORT")
    if report_path:
        Path(report_path).write_text(message, encoding="utf-8")


def available_port(preferred: int = PREFERRED_PORT) -> int:
    """Use the familiar port when free, otherwise choose a safe local port."""
    for candidate in (preferred, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((HOST, candidate))
            except OSError:
                continue
            return int(probe.getsockname()[1])
    raise RuntimeError("No local port is available for MiND")


def wait_until_ready(url: str, timeout: float = STARTUP_TIMEOUT_SECONDS) -> bool:
    """Wait for the local health endpoint without contacting external services."""
    deadline = time.monotonic() + timeout
    health_url = f"{url}/v1/health"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=0.5) as response:
                return response.status == 200
        except OSError:
            time.sleep(0.1)
    return False


class LocalMindServer:
    """Run Uvicorn in the background while the desktop controller is open."""

    def __init__(self, port: Optional[int] = None):
        import uvicorn

        from nemosine_mind.main import app

        self.port = port if port is not None else available_port()
        self.url = f"http://{HOST}:{self.port}"
        config = uvicorn.Config(
            app,
            host=HOST,
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(
            target=self.server.run,
            name="mind-local-server",
            daemon=True,
        )

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.should_exit = True
        if self.thread.is_alive():
            self.thread.join(timeout=3.0)


def smoke_test() -> int:
    """Exercise the same packaged server used by the desktop shortcut."""
    # Providers are bundled for the next UI increment. Importing both here makes
    # the packaging smoke test prove that their SDKs survived freezing.
    from anthropic import Anthropic
    from openai import OpenAI

    assert Anthropic is not None
    assert OpenAI is not None
    write_smoke_report("providers loaded")
    local = LocalMindServer()
    local.start()
    try:
        if not wait_until_ready(local.url):
            write_smoke_report("local health endpoint timed out")
            return 1
        with urllib.request.urlopen(local.url, timeout=2.0) as response:
            page = response.read().decode("utf-8")
        required_markers = (
            "Central de interação auditável",
            "mind-logo.svg",
            "Seletor de LLM",
            "Plug and Play",
            "Verificar atualizações",
            "Exportar dados",
            "Limpar dados",
            "Fazer backup",
        )
        missing = [marker for marker in required_markers if marker not in page]
        if missing:
            write_smoke_report(f"missing UI markers: {missing}")
            return 1
        with urllib.request.urlopen(
            f"{local.url}/ui/assets/mind-logo.svg", timeout=2.0
        ) as response:
            logo = response.read().decode("utf-8")
        if 'aria-label="MiND"' not in logo:
            write_smoke_report("new MiND logo was not found")
            return 1
        write_smoke_report("ok: MiND 1.0.3 visual control center")
        return 0
    finally:
        local.stop()


def desktop_main() -> int:
    """Open a small, native controller and the real MiND interface."""
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk()
    root.title("MiND — Interface local")
    root.geometry("430x220")
    root.resizable(False, False)

    frame = ttk.Frame(root, padding=28)
    frame.pack(fill="both", expand=True)

    title = ttk.Label(frame, text="MiND", font=("Segoe UI", 20, "bold"))
    title.pack(anchor="w")
    subtitle = ttk.Label(
        frame,
        text="Central local de interações auditáveis",
        font=("Segoe UI", 10),
    )
    subtitle.pack(anchor="w", pady=(0, 18))

    status_text = tk.StringVar(value="Iniciando o serviço local…")
    status = ttk.Label(frame, textvariable=status_text, font=("Segoe UI", 10))
    status.pack(anchor="w")

    actions = ttk.Frame(frame)
    actions.pack(fill="x", pady=(22, 0))
    open_button = ttk.Button(actions, text="Abrir interface", state="disabled")
    open_button.pack(side="left")
    close_button = ttk.Button(actions, text="Encerrar MiND")
    close_button.pack(side="right")

    local = LocalMindServer()
    local.start()
    opened = False
    started_at = time.monotonic()

    def open_interface() -> None:
        webbrowser.open(local.url)

    def close_application() -> None:
        close_button.configure(state="disabled")
        status_text.set("Encerrando o MiND…")
        local.stop()
        root.destroy()

    def check_startup() -> None:
        nonlocal opened
        if wait_until_ready(local.url, timeout=0.2):
            status_text.set("MiND está ativo somente neste computador.")
            open_button.configure(state="normal", command=open_interface)
            if not opened:
                opened = True
                open_interface()
            return
        if time.monotonic() - started_at >= STARTUP_TIMEOUT_SECONDS:
            messagebox.showerror(
                "MiND",
                "Não foi possível iniciar a interface local. Feche esta janela e "
                "tente novamente.",
            )
            close_application()
            return
        root.after(250, check_startup)

    close_button.configure(command=close_application)
    root.protocol("WM_DELETE_WINDOW", close_application)
    root.after(100, check_startup)
    root.mainloop()
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--smoke-test", action="store_true")
    args, _ = parser.parse_known_args(argv)
    try:
        return smoke_test() if args.smoke_test else desktop_main()
    except Exception as exc:
        if args.smoke_test:
            write_smoke_report(f"{type(exc).__name__}: {exc}")
        if not args.smoke_test:
            try:
                from tkinter import messagebox

                messagebox.showerror("MiND", f"Falha ao iniciar: {exc}")
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
