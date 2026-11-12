import os
import sys
import time
import socket
import subprocess
import webbrowser

def is_server_running(host="127.0.0.1", port=8080):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0

def main():
    target_url = "http://localhost:8080/shop-login/"

    print("=" * 72)
    print("         KEP PRINTGRID - SHOP OWNER INTERFACE LAUNCHER")
    print("=" * 72)
    print(f" [✓] Shop Owner Login      : http://localhost:8080/shop-login/")
    print(f" [✓] Register New Shop     : http://localhost:8080/register-shop/")
    print(f" [✓] Printer Management    : http://localhost:8080/printers/list/")
    print(f" [✓] Add HP Smart Tank 530 : http://localhost:8080/printers/add/")
    print(f" [✓] Pricing Rules Config  : http://localhost:8080/pricing/")
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
        print(f"[✓] Opening Shop Owner Login in your browser:\n    -> {target_url}\n")
        print("  Test Credentials:")
        print("    Owner Username : metro_owner")
        print("    Password       : MetroPrint2026!\n")
        webbrowser.open(target_url)
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
