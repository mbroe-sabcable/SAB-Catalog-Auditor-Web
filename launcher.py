import socket
import threading
import time
import webbrowser

import uvicorn

from main import app

HOST = "127.0.0.1"
START_PORT = 8000


def _find_available_port():
    port = START_PORT
    while port <= 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((HOST, port))
            except OSError:
                port += 1
                continue
            return port

    raise RuntimeError("No available local port found for the SAB Catalog Auditor")


def _wait_for_server(port, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main():
    port = _find_available_port()
    url = f"http://{HOST}:{port}"
    config = uvicorn.Config(app, host=HOST, port=port, log_level="info")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, name="uvicorn", daemon=True)
    server_thread.start()

    if not _wait_for_server(port):
        server.should_exit = True
        server_thread.join()
        raise RuntimeError(f"SAB Catalog Auditor did not start at {url}")

    webbrowser.open(url)

    try:
        while server_thread.is_alive():
            server_thread.join(timeout=0.5)
    except KeyboardInterrupt:
        server.should_exit = True
        server_thread.join()
    finally:
        server.should_exit = True
        if server_thread.is_alive():
            server_thread.join()


if __name__ == "__main__":
    main()
