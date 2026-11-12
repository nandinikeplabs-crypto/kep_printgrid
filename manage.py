#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kep_printgrid.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # If run in VS Code without arguments (e.g. clicking the Run button),
    # default to starting the development server on 0.0.0.0:8080
    if len(sys.argv) == 1:
        import socket
        lan_ip = "127.0.0.1"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                lan_ip = s.getsockname()[0]
        except Exception:
            pass

        print("=" * 72)
        print("          KEP PRINTGRID - ZERO-KNOWLEDGE PRINT AUTOMATION")
        print("=" * 72)
        print(" [✓] Laptop Browser URL   : http://localhost:8080/ (or http://127.0.0.1:8080/)")
        print(f" [✓] Mobile Phone Wi-Fi   : http://{lan_ip}:8080/shop/KEP10001/")
        print(" [✓] Live Camera Scanner  : http://localhost:8080/scanner/")
        print(" [✓] Shop Owner Dashboard : http://localhost:8080/shop-login/")
        print("=" * 72)
        print(" NOTE: In Chrome on this laptop, ALWAYS use http://localhost:8080/")
        print("       Do NOT type http://0.0.0.0:8080/ into Chrome (causes ERR_ADDRESS_INVALID)")
        print("=" * 72 + "\n")
        sys.argv = [sys.argv[0], 'runserver', '0.0.0.0:8080']

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
