"""
KEP PrintGrid - Main VS Code Application Runner & All-in-One Engine
=====================================================================
Runs:
 1. Django Web Application bound to 0.0.0.0:8080
 2. Integrated Background Windows Print Spooler Connector for HP Smart Tank 530
 3. Optional Public HTTPS Tunnel for Mobile Data (Jio/Airtel 4G/5G) Customer QR Scanning

Usage:
  python run_app.py              (Local Wi-Fi + Spooler)
  python run_app.py --tunnel     (Public Mobile Data QR + Wi-Fi + Spooler)
"""

import os
import sys
import time
import socket
import subprocess
import threading
import argparse
import webbrowser

def get_lan_ip():
    """Detect the machine's local Wi-Fi IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def is_port_open(host="127.0.0.1", port=8080):
    """Check if port 8080 is reachable."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.8)
        return s.connect_ex((host, port)) == 0

def init_django():
    """Initializes Django environment."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kep_printgrid.settings')
    import django
    django.setup()

def get_active_shop_info():
    """Retrieves active shop, token, and default printer."""
    init_django()
    from core.models import Shop
    from printers.models import Printer
    from core.services.qr_service import generate_shop_qr_code

    # Prefer latest active shop (e.g. mm xerox or user shop)
    shop = Shop.objects.order_by('-created_at').first() or Shop.objects.first()
    if not shop:
        return None, None, "No Shop Found", "No Printer"

    # Prioritize printer assigned to the shop's QR code
    qr_printer = getattr(shop, 'qr_code', None) and shop.qr_code.assigned_printer
    default_printer = qr_printer or Printer.objects.filter(shop=shop, is_default=True).first() or Printer.objects.filter(shop=shop).first()
    printer_name = default_printer.name if default_printer else "HP Smart Tank 530 (Color & B&W)"

    # Ensure QR code assets are up-to-date
    try:
        generate_shop_qr_code(shop)
    except Exception as e:
        print(f"[*] Note: QR code generation notice: {e}")

    return shop, default_printer, shop.name, printer_name

def start_public_tunnel(port=8080):
    """
    Starts a free HTTPS tunnel using available tools (Cloudflare, pinggy, or localtunnel).
    Returns the public URL string or None.
    """
    print("[*] Starting Public HTTPS Tunnel for Mobile Data customers...")

    # Method 1: Check if cloudflared is installed
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for _ in range(30):
            line = proc.stdout.readline()
            if "trycloudflare.com" in line:
                for word in line.split():
                    if "trycloudflare.com" in word:
                        url = word.strip().rstrip('.,;')
                        if not url.startswith('http'):
                            url = 'https://' + url
                        return url, proc
            time.sleep(0.3)
    except FileNotFoundError:
        pass

    # Method 2: Try localtunnel via npx
    try:
        proc = subprocess.Popen(
            ["cmd", "/c", "npx", "--yes", "localtunnel", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for _ in range(30):
            line = proc.stdout.readline()
            if "url is:" in line.lower() or "loca.lt" in line.lower():
                for word in line.split():
                    if "loca.lt" in word:
                        url = word.strip().rstrip('.,;')
                        if not url.startswith('http'):
                            url = 'https://' + url
                        return url, proc
            time.sleep(0.3)
    except Exception:
        pass

    # Method 3: Try built-in OpenSSH with pinggy
    try:
        proc = subprocess.Popen(
            ["ssh", "-p", "443", "-R0:localhost:8080", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "qr@a.pinggy.io"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for _ in range(40):
            line = proc.stdout.readline()
            if "http://" in line or "https://" in line:
                for word in line.split():
                    if "pinggy.link" in word or "a.pinggy.io" in word:
                        url = word.strip().rstrip('.,;')
                        if url.startswith('http://'):
                            url = url.replace('http://', 'https://')
                        return url, proc
            time.sleep(0.3)
    except Exception:
        pass

    return None, None

def main():
    parser = argparse.ArgumentParser(description="KEP PrintGrid All-In-One Runner")
    parser.add_argument("--tunnel", action="store_true", help="Launch public HTTPS tunnel for Mobile Data customer QR codes")
    parser.add_argument("--public-url", type=str, default="", help="Custom public URL or ngrok domain")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    lan_ip = get_lan_ip()

    # Retrieve shop & printer information
    shop, default_printer, shop_name, printer_name = get_active_shop_info()
    shop_code = getattr(shop, 'shop_code', 'KEP37105')
    shop_slug = getattr(shop, 'slug', 'kep-xerox-2458f624')
    shop_token = getattr(shop, 'connector_auth_token', '')

    public_url = args.public_url or os.getenv('PUBLIC_URL', '')
    tunnel_proc = None

    if (args.tunnel or os.getenv('USE_TUNNEL', '').lower() in ('true', '1')) and not public_url:
        tunnel_url, tunnel_proc = start_public_tunnel(8080)
        if tunnel_url:
            public_url = tunnel_url
            os.environ['PUBLIC_URL'] = public_url

    # Regenerate QR codes with public URL if available
    if public_url and shop:
        os.environ['PUBLIC_URL'] = public_url
        try:
            from core.services.qr_service import generate_shop_qr_code
            generate_shop_qr_code(shop)
        except Exception:
            pass

    print("\n" + "=" * 78)
    print("      KEP PRINTGRID - SMART XEROX PLATFORM & AUTOMATED PRINT ENGINE")
    print("=" * 78)
    print(f" [✓] Shop Name           : {shop_name} (Code: {shop_code})")
    print(f" [✓] Connected Printer   : {printer_name}")
    print(f" [✓] Local Machine IP    : {lan_ip}")
    print("-" * 78)
    if public_url:
        print(f" 📱 MOBILE DATA QR URL   : {public_url}/shop/{shop_code}/")
        print("    (Scan using Jio, Airtel, Vi, 4G/5G mobile internet from anywhere!)")
    else:
        print(" 📱 MOBILE DATA ACCESS   : To enable 4G/5G Mobile Data scanning, run with: python run_app.py --tunnel")

    print(f" 🛜 LOCAL WI-FI URL      : http://{lan_ip}:8080/shop/{shop_code}/")
    print(f" 💻 LAPTOP ADMIN URL     : http://localhost:8080/shop-login/")
    print(f" 🖨️ PRINTER AUTO-SPOOLER : Active & Auto-Routing to {printer_name}")
    print("=" * 78)
    print(" NOTE: Keep this terminal window open while printing.")
    print("=" * 78 + "\n")

    # 1. Start Django Web Server
    server_proc = None
    if not is_port_open():
        print("[*] Starting KEP PrintGrid Web Server on 0.0.0.0:8080...")
        manage_path = os.path.join(base_dir, "manage.py")
        server_proc = subprocess.Popen([sys.executable, manage_path, "runserver", "0.0.0.0:8080"])

        for _ in range(20):
            time.sleep(0.5)
            if is_port_open():
                break

    if is_port_open():
        print("[✓] Web Server is LIVE and ready!")
    else:
        print("[!] Server process started. Listening on port 8080.")

    # 2. Start Automatic Background Windows Printer Spooler Connector
    connector_proc = None
    if shop_token:
        print(f"[*] Starting Printer Auto-Spooler for '{printer_name}'...")
        connector_script = os.path.join(base_dir, "connector", "run_connector.py")
        connector_cmd = [
            sys.executable,
            connector_script,
            "--server", "http://127.0.0.1:8080",
            "--token", shop_token,
            "--shop", shop_slug,
            "--spooler", "windows",
            "--interval", "2"
        ]
        try:
            connector_proc = subprocess.Popen(connector_cmd)
            print(f"[✓] Printer Auto-Spooler is RUNNING. Paid documents will print automatically!")
        except Exception as e:
            print(f"[!] Warning: Could not launch connector subprocess: {e}")

    # Open admin browser
    try:
        webbrowser.open("http://localhost:8080/shop-login/")
    except Exception:
        pass

    print("\n[READY] KEP PrintGrid is operational. Press Ctrl+C in this terminal to stop.\n")

    try:
        while True:
            time.sleep(1)
            if server_proc and server_proc.poll() is not None:
                print("\nServer process ended.")
                break
    except KeyboardInterrupt:
        print("\n\nShutting down KEP PrintGrid cleanly...")
        if connector_proc:
            print("[*] Stopping printer spooler...")
            connector_proc.terminate()
            try:
                connector_proc.wait(timeout=3)
            except Exception:
                pass

        if server_proc:
            print("[*] Stopping web server...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=3)
            except Exception:
                pass

        if tunnel_proc:
            print("[*] Stopping public tunnel...")
            tunnel_proc.terminate()

        print("[✓] All services stopped cleanly.")

if __name__ == "__main__":
    main()
