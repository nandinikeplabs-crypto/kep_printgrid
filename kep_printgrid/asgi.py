"""
ASGI config for kep_printgrid project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kep_printgrid.settings')

application = get_asgi_application()

if __name__ == '__main__':
    import socket
    lan_ip = "127.0.0.1"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
    except Exception:
        pass

    import uvicorn
    print("\n" + "=" * 72)
    print("      KEP PRINTGRID - ASGI UVICORN SERVER (RUNNING FROM VS CODE)")
    print("=" * 72)
    print(" [✓] Laptop Browser URL   : http://localhost:8080/ (or http://127.0.0.1:8080/)")
    print(f" [✓] Mobile Phone Wi-Fi   : http://{lan_ip}:8080/shop/KEP10001/")
    print(" [✓] Live Camera Scanner  : http://localhost:8080/scanner/")
    print(" [✓] Shop Owner Login     : http://localhost:8080/shop-login/")
    print("=" * 72)
    print(" NOTE: In Chrome on this laptop, ALWAYS open http://localhost:8080/")
    print("       Do NOT type http://0.0.0.0:8080/ (causes ERR_ADDRESS_INVALID)")
    print("=" * 72 + "\n")
    uvicorn.run("kep_printgrid.asgi:application", host="0.0.0.0", port=8080, reload=True)
