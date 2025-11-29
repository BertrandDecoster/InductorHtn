#!/usr/bin/env python3
"""
Start the InductorHTN GUI - launches backend, frontend, and opens browser.

Usage:
    python start_gui.py           # Start everything
    python start_gui.py --no-browser  # Start without opening browser
"""

import subprocess
import sys
import os
import time
import webbrowser
import signal
import argparse

# Configuration
BACKEND_PORT = 5000
FRONTEND_PORT = 5173
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"

# Get paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
FRONTEND_DIR = os.path.join(SCRIPT_DIR, "frontend")

# Find the correct Python executable (venv)
def get_python_executable():
    """Get the venv Python executable"""
    if sys.platform == "win32":
        venv_python = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")

    if os.path.exists(venv_python):
        return venv_python
    # Fallback to current Python
    return sys.executable

PYTHON_EXE = get_python_executable()

processes = []

def cleanup(signum=None, frame=None):
    """Kill all child processes on exit"""
    print("\n\nShutting down...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()
    print("Done.")
    sys.exit(0)

def wait_for_server(url, timeout=30):
    """Wait for a server to become available"""
    import urllib.request
    import urllib.error

    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(0.5)
    return False

def main():
    parser = argparse.ArgumentParser(description="Start InductorHTN GUI")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    # Register cleanup handler
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, cleanup)

    print("=" * 60)
    print("InductorHTN GUI Launcher")
    print("=" * 60)

    # Start backend
    print(f"\n[1/3] Starting Flask backend on port {BACKEND_PORT}...")
    print(f"      Using Python: {PYTHON_EXE}")
    backend_proc = subprocess.Popen(
        [PYTHON_EXE, "app.py"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(backend_proc)

    # Wait for backend to be ready
    print("      Waiting for backend to start...")
    if wait_for_server(f"{BACKEND_URL}/health", timeout=15):
        print(f"      Backend ready at {BACKEND_URL}")
    else:
        print("      ERROR: Backend failed to start!")
        cleanup()

    # Start frontend
    print(f"\n[2/3] Starting Vite frontend on port {FRONTEND_PORT}...")

    # Use npm.cmd on Windows, npm elsewhere
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(frontend_proc)

    # Wait for frontend to be ready
    print("      Waiting for frontend to start...")
    time.sleep(3)  # Give Vite a moment to start
    if wait_for_server(FRONTEND_URL, timeout=30):
        print(f"      Frontend ready at {FRONTEND_URL}")
    else:
        print("      WARNING: Could not verify frontend is running")

    # Open browser
    if not args.no_browser:
        print(f"\n[3/3] Opening browser...")
        time.sleep(1)
        webbrowser.open(FRONTEND_URL)
    else:
        print(f"\n[3/3] Skipping browser (--no-browser)")

    print("\n" + "=" * 60)
    print(f"GUI is running!")
    print(f"  Frontend: {FRONTEND_URL}")
    print(f"  Backend:  {BACKEND_URL}")
    print("=" * 60)
    print("\nPress Ctrl+C to stop all servers\n")

    # Keep running and forward output from backend
    import select
    import threading

    def read_backend_output():
        """Thread to read and display backend output"""
        try:
            for line in backend_proc.stdout:
                print(f"[BACKEND] {line}", end='')
        except:
            pass

    # Start thread to read backend output
    backend_thread = threading.Thread(target=read_backend_output, daemon=True)
    backend_thread.start()

    try:
        while True:
            # Check if processes are still running
            if backend_proc.poll() is not None:
                print("Backend process exited unexpectedly!")
                break
            if frontend_proc.poll() is not None:
                print("Frontend process exited unexpectedly!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    cleanup()

if __name__ == "__main__":
    main()
