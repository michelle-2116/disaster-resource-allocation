import os
import sys
import subprocess
import threading
import time

# Color codes
COLOR_RESET = "\033[0m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_MAGENTA = "\033[35m"
COLOR_GRAY = "\033[90m"

# Enable virtual terminal processing on Windows for ANSI colors
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        h_std_out = kernel32.GetStdHandle(-11) # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(h_std_out, ctypes.byref(mode)):
            kernel32.SetConsoleMode(h_std_out, mode.value | 4) # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass

services = [
    {
        "name": "DI-Backend",
        "color": COLOR_CYAN,
        "dir": "DataIngestion-Allocation/backend",
        "command": "uvicorn src.api:app --port 8000 --reload"
    },
    {
        "name": "Frontend",
        "color": COLOR_GREEN,
        "dir": "DataIngestion-Allocation/frontend",
        "command": "npm run dev"
    },
    {
        "name": "RO-Backend",
        "color": COLOR_YELLOW,
        "dir": "Route-Optimizer/backend",
        "command": "uvicorn main:app --port 8001 --reload"
    },
    {
        "name": "Discord-Bot",
        "color": COLOR_MAGENTA,
        "dir": "DataIngestion-Allocation/backend",
        "command": "python -m src.discord_listener"
    }
]

processes = []

def stream_output(pipe, prefix, color):
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                trimmed = line.strip()
                if trimmed:
                    print(f"{color}[{prefix}]{COLOR_RESET} {trimmed}")
    except Exception:
        pass

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if not root_dir:
        root_dir = "."
    
    print("========================================")
    print("  Disaster Resource Allocation System")
    print("  Starting all services...")
    print("========================================")
    print()

    for svc in services:
        name = svc["name"]
        color = svc["color"]
        subdir = os.path.join(root_dir, svc["dir"])
        cmd = svc["command"]

        print(f"{COLOR_GRAY}[BOOT] {color}{name}{COLOR_GRAY} -> {cmd}{COLOR_RESET}")

        # Start process with stdout and stderr redirected to pipes
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=subdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        processes.append((proc, name))

        # Start background threads to stream output
        t_out = threading.Thread(target=stream_output, args=(proc.stdout, name, color), daemon=True)
        t_err = threading.Thread(target=stream_output, args=(proc.stderr, name, color), daemon=True)
        t_out.start()
        t_err.start()

    print()
    print(f"{COLOR_GREEN}[OK] All services launched. Press Ctrl+C to stop all.{COLOR_RESET}")
    print()
    print(f"  DI-Backend   -> http://127.0.0.1:8000")
    print(f"  Frontend     -> http://localhost:5173")
    print(f"  RO-Backend   -> http://127.0.0.1:8001")
    print(f"  Discord-Bot  -> (Running Discord Ingestion listener...)")
    print()
    print(f"{COLOR_GRAY}────────────────────────────────────────{COLOR_RESET}")
    print()

    # Keep main thread alive and monitor processes
    try:
        while True:
            # Check if all processes have exited
            all_dead = True
            for proc, name in processes:
                if proc.poll() is None:
                    all_dead = False
            if all_dead:
                print(f"\n{COLOR_GRAY}[DONE] All services have exited.{COLOR_RESET}")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n[STOP] Shutting down all services...")
    finally:
        cleanup()

def cleanup():
    # Terminate all processes
    for proc, name in processes:
        if proc.poll() is None:
            print(f"  Stopping {name}...")
            if os.name == 'nt':
                # Force kill process and all its children using Windows taskkill
                subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                proc.terminate()
                proc.wait()
    print("[DONE] All services stopped.")

if __name__ == "__main__":
    main()
