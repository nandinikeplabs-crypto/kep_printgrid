import argparse
import logging
import sys
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from connector.client import PrintGridConnectorClient


def main():
    parser = argparse.ArgumentParser(description="KEP PrintGrid Windows Local Printer Connector")
    parser.add_argument("--server", default="http://127.0.0.1:8000", help="KEP PrintGrid Cloud Backend URL")
    parser.add_argument("--token", required=True, help="Shop Connector Authentication Token")
    parser.add_argument("--shop", default="", help="Shop Unique Slug (optional)")
    parser.add_argument("--spooler", choices=['auto', 'windows', 'dev'], default='auto', help="Print Spooler backend")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run a single heartbeat and job polling pass then exit")

    args = parser.parse_args()

    client = PrintGridConnectorClient(
        server_url=args.server,
        auth_token=args.token,
        shop_slug=args.shop,
        spooler_mode=args.spooler
    )

    try:
        client.run(poll_interval=args.interval, run_once=args.once)
    except KeyboardInterrupt:
        print("\nStopping KEP PrintGrid Connector cleanly...")


if __name__ == "__main__":
    main()
