import os
import sys
import time
import socket
import subprocess
import webbrowser

def get_lan_ip():
    """Detect active Wi-Fi IPv4 address dynamically."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def is_server_running(host="127.0.0.1", port=8080):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0

def main():
    lan_ip = get_lan_ip()
    local_url = "http://localhost:8080/shop/KEP10001/"
    mobile_url = f"http://{lan_ip}:8080/shop/KEP10001/"

    print("=" * 72)
    print("         KEP PRINTGRID - USER / CUSTOMER INTERFACE LAUNCHER")
    print("=" * 72)
    print(f" [✓] Laptop Browser URL   : {local_url}")
    print(f" [✓] Mobile Phone on Wi-Fi: {mobile_url}")
    print(f" [✓] Live Camera Scanner  : http://localhost:8080/scanner/")
    print("=" * 72)

    proc = None
    if not is_server_running():
        print("[*] Web server not running yet. Starting server on 0.0.0.0:8080...")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        manage_path = os.path.join(base_dir, "manage.py")
        proc = subprocess.Popen([sys.executable, manage_path, "runserver", "0.0.0.0:8080"])

        # Wait up to 10 seconds for port 8080 to become available
        for _ in range(20):
            time.sleep(0.5)
            if is_server_running():
                break

    if is_server_running():
        print("[✓] Server is active on port 8080.")
        print(f"[✓] Opening Customer Ordering Page in your browser:\n    -> {local_url}\n")
        webbrowser.open(local_url)
    else:
        print("[!] Could not connect to port 8080. Please run 'python run_app.py' manually.")

    if proc:
        print("[INFO] Press Ctrl+C anytime in this terminal to stop the server.\n")
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    main()
