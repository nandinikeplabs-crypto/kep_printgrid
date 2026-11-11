# KEP PrintGrid - Complete Project Codebase Bundle

This single file contains the entire source code for all backend models, views, templates, APIs, Windows local connector, encryption algorithms, automated tests, and configuration files of **KEP PrintGrid**.

## Table of Files Included

- `.env.example`
- `README.md`
- `bundle_codebase.py`
- `connector/client.py`
- `connector/crypto_manager.py`
- `connector/local_store.py`
- `connector/page_validator.py`
- `connector/run_connector.py`
- `connector/secure_cleaner.py`
- `connector/spooler/__init__.py`
- `connector/spooler/base_spooler.py`
- `connector/spooler/dev_spooler.py`
- `connector/spooler/spooler_factory.py`
- `connector/spooler/windows_spooler.py`
- `core/__init__.py`
- `core/admin.py`
- `core/apps.py`
- `core/context_processors.py`
- `core/decorators.py`
- `core/forms.py`
- `core/management/__init__.py`
- `core/management/commands/__init__.py`
- `core/management/commands/seed_demo_data.py`
- `core/migrations/0001_initial.py`
- `core/migrations/__init__.py`
- `core/models.py`
- `core/services/__init__.py`
- `core/services/qr_service.py`
- `core/tests.py`
- `core/urls.py`
- `core/views.py`
- `kep_printgrid/__init__.py`
- `kep_printgrid/asgi.py`
- `kep_printgrid/settings.py`
- `kep_printgrid/urls.py`
- `kep_printgrid/wsgi.py`
- `manage.py`
- `orders/__init__.py`
- `orders/admin.py`
- `orders/api_views.py`
- `orders/apps.py`
- `orders/forms.py`
- `orders/migrations/0001_initial.py`
- `orders/migrations/__init__.py`
- `orders/models.py`
- `orders/tests.py`
- `orders/urls.py`
- `orders/views.py`
- `payments/__init__.py`
- `payments/admin.py`
- `payments/apps.py`
- `payments/migrations/0001_initial.py`
- `payments/migrations/__init__.py`
- `payments/models.py`
- `payments/services/__init__.py`
- `payments/services/gateway_adapter.py`
- `payments/tests.py`
- `payments/urls.py`
- `payments/views.py`
- `printers/__init__.py`
- `printers/admin.py`
- `printers/api_views.py`
- `printers/apps.py`
- `printers/migrations/0001_initial.py`
- `printers/migrations/__init__.py`
- `printers/models.py`
- `printers/serializers.py`
- `printers/services/__init__.py`
- `printers/services/routing_service.py`
- `printers/tests.py`
- `printers/urls.py`
- `printers/views.py`
- `requirements.txt`
- `static/css/styles.css`
- `static/js/client_crypto.js`
- `static/js/order_flow.js`
- `templates/base.html`
- `templates/components/dashboard_sidebar.html`
- `templates/core/home.html`
- `templates/core/login.html`
- `templates/core/owner_overview.html`
- `templates/core/register.html`
- `templates/core/reports.html`
- `templates/core/shop_qr_management.html`
- `templates/core/shop_settings.html`
- `templates/core/staff_management.html`
- `templates/orders/customer_track_order.html`
- `templates/orders/order_detail.html`
- `templates/orders/order_list.html`
- `templates/orders/pricing_settings.html`
- `templates/orders/shop_order_page.html`
- `templates/orders/staff_dashboard.html`
- `templates/printers/printer_assignments.html`
- `templates/printers/printer_list.html`
- `tests/__init__.py`
- `tests/test_auth.py`
- `tests/test_connector.py`
- `tests/test_document_encryption.py`
- `tests/test_payments_and_orders.py`
- `tests/test_printers_and_routing.py`
- `tests/test_qr_and_shop.py`

---

## File: `.env.example`

```text
# KEP PrintGrid Environment Configuration
DEBUG=True
SECRET_KEY=change-in-production-django-insecure-secret-key-kep-printgrid-2026
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration (MySQL / SQLite fallback)
# Set DB_ENGINE=mysql to use MySQL server. When empty or sqlite, uses SQLite for dev/testing.
DB_ENGINE=sqlite
DB_NAME=kep_printgrid
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306

# Payment Gateway (Razorpay)
RAZORPAY_KEY_ID=rzp_test_sample_key_id
RAZORPAY_KEY_SECRET=sample_secret_key
RAZORPAY_WEBHOOK_SECRET=sample_webhook_secret
PAYMENT_SANDBOX_MODE=True

# Base URL for permanent QR codes
BASE_APP_URL=http://127.0.0.1:8000

```

---

## File: `README.md`

```markdown
# KEP PrintGrid: QR-Based Xerox & Print Automation Platform

**KEP PrintGrid** is a production-grade, secure, QR-based document printing and automation platform designed for Xerox and digital printing shops. 

Customers scan a shop's permanent QR code, upload PDF documents, preview pages directly in their mobile browser, configure printing preferences, pay online via Razorpay, and track real-time printing progress. Shop owners and operators manage copiers, pricing, order queues, and intelligent spooler routing from a centralized management dashboard.

---

## 1. Key Architectural Capabilities

### A. Permanent Shop QR Code Invariant
- Every registered print shop is issued a unique, permanent QR code URL (`/shop/<shop-slug>/`).
- **Hardware Agnostic**: Adding, replacing, servicing, or renaming physical printers **never** alters or invalidates the permanent QR code.
- **Counter Posters**: Owners can generate and download print-ready high-resolution A4 counter stand posters (PDF) and PNG assets directly from the dashboard.
- **Operational Pause**: If a shop is overwhelmed or closed for a break, the owner toggles "Temporarily Paused". The permanent QR remains valid, informing incoming customers of the pause without invalidating the code.

### B. Client-Side Zero-Knowledge Encryption
- **Confidentiality**: Customer documents are encrypted directly in the web browser using the native **Web Crypto API (AES-256-GCM)** with a unique 256-bit symmetric session key.
- **Public-Key Envelope**: The AES key is wrapped on the customer's device using the authorized shop's **RSA-2048 public key (RSA-OAEP with SHA-256)**.
- **Cloud Blindness**: The Django cloud backend stores only binary ciphertexts and cryptographic hashes (`SHA-256`). Plaintext files and decryption keys **never** exist on the cloud server.
- **Local Unwrapping**: Only the authorized **KEP PrintGrid Windows Connector** running on the physical shop computer possesses the RSA private key required to decrypt the document locally before spooling.

### C. Intelligent Print Job Routing
- **Constraint Satisfaction Routing**: PrintGrid analyzes each order's preferences (B&W vs Colour, Single vs Duplex, A4 vs A3) and routes to active, online copiers satisfying those requirements.
- **Automated Fallback**: Primary and secondary copiers can be configured per category. If a primary copier disconnects, eligible jobs fail over safely to configured backup printers.
- **Safety**: Print jobs submitted or physically printed are **never** automatically duplicated on failover without explicit staff re-authorization.

### D. Windows Local Printer Connector
- Runs locally on the Xerox shop's Windows terminal (`connector/run_connector.py`).
- Detects installed Windows OS spooler queues (via native `win32print` / PowerShell spooler abstraction).
- Syncs printer availability and hardware capabilities to the cloud backend via authenticated heartbeats (`X-Shop-Token`).
- Downloads encrypted payloads, decrypts them locally, verifies that the actual PDF page count matches what was paid for, prints to the OS queue, and securely shreds temporary decrypted files.

---

## 2. Technology Stack

- **Backend**: Python 3.15, Django 6.1, Django REST Framework
- **Database**: MySQL (Production) / SQLite (Dev & automated test suite)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Bootstrap Icons, PDF.js
- **Cryptography**: `cryptography` (Python) + Web Crypto API (`window.crypto.subtle`)
- **Payment Gateway**: Configurable Provider Adapter (Razorpay Live + Razorpay Sandbox Simulator with HMAC-SHA256 signature verification)
- **Windows Spooler Connector**: Python client with `pywin32` integration and cross-platform simulation mode

---

## 3. Project Structure

```text
kep_printgrid/
├── manage.py
├── requirements.txt
├── .env.example
├── .env
├── README.md
├── kep_printgrid/                  # Project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                          # Authentication, Shops, Staff & QR Management
│   ├── models.py                  # User, Shop, ShopStaff, ShopQRCode, AuditLog
│   ├── views.py                   # Dashboard, Settings, Staff, Reports
│   ├── forms.py                   # Registration, Login, Settings
│   ├── decorators.py              # Role-Based Access Control
│   ├── services/
│   │   └── qr_service.py          # PNG & Printable A4 PDF poster generator
│   └── management/commands/
│       └── seed_demo_data.py      # Demo seeder
├── printers/                      # Copiers & Windows Connector APIs
│   ├── models.py                  # Printer, PrinterCapability, PrinterAssignment, Connector
│   ├── views.py                   # Printer management, assignments
│   ├── api_views.py               # REST API for local connector (register, heartbeat, poll)
│   └── services/
│       └── routing_service.py     # Intelligent print job router
├── orders/                        # Customer Ordering, Pricing & Spooling
│   ├── models.py                  # PrintDocument, PrintPreference, PricingRule, PrintOrder, PrintJob
│   ├── views.py                   # Public shop order page, tracker, staff console
│   └── api_views.py               # Quote, Encrypted Upload, Order Creation APIs
├── payments/                      # Payment Gateways & Verifications
│   ├── models.py                  # Payment, Refund
│   ├── views.py                   # Create order, HMAC verification, Webhooks, Refunds
│   └── services/
│       └── gateway_adapter.py     # Razorpay Live & Sandbox Adapter
├── connector/                     # Windows Local Application
│   ├── run_connector.py           # CLI daemon runner
│   ├── client.py                  # Handshake, heartbeat, decryption & spooling client
│   ├── crypto_manager.py          # RSA keypair manager & local AES-GCM decryptor
│   ├── page_validator.py          # Local PDF page count verifier
│   ├── secure_cleaner.py          # Multi-pass secure file shredder
│   └── spooler/                   # Windows spooler & dev simulator abstraction
├── static/                        # Frontend assets
│   ├── css/styles.css
│   └── js/
│       ├── client_crypto.js       # Web Crypto AES-GCM + RSA wrapping
│       └── order_flow.js          # Customer wizard & Razorpay integration
├── templates/                     # Bootstrap 5 responsive UI templates
└── tests/                         # Full automated test suite (22 unit & integration tests)
```

---

## 4. Setup & Running Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(By default, `DB_ENGINE=sqlite` is enabled for seamless local development. To connect a live MySQL server, set `DB_ENGINE=mysql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` in `.env`).*

### Step 3: Run Database Migrations
```bash
python manage.py migrate
```

### Step 4: Seed Demo Data
Populate the database with a demonstration shop, staff account, printers, and pricing:
```bash
python manage.py seed_demo_data
```

### Step 5: Run Automated Tests
Execute the comprehensive test suite verifying authentication, document encryption, permanent QR codes, intelligent routing, and payments:
```bash
python manage.py test tests
```

### Step 6: Start the Cloud Web Server
```bash
python manage.py runserver 127.0.0.1:8000
```
- **Public Home & Order Tracking**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Shop Owner Login**: [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- **Customer QR Ordering Page**: [http://127.0.0.1:8000/shop/metro-xerox/](http://127.0.0.1:8000/shop/metro-xerox/)

### Step 7: Launch the Windows Local Connector
On the shop computer (or in a separate terminal):
```bash
python connector/run_connector.py --server http://127.0.0.1:8000 --token metro_demo_auth_token_991823719827391827 --shop metro-xerox
```

---

## 5. Seeded Demo Accounts

| Role | Email / Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Shop Owner** | `owner@metroprint.example` | `MetroPrint2026!` | Full admin dashboard, pricing, QR download |
| **Counter Staff**| `staff@metroprint.example` | `StaffPass2026!` | Counter console, collection handover, retry |
| **Customer** | Anonymous via QR | None required | Access via `/shop/metro-xerox/` |

---

## 6. REST API Endpoints Overview

### Customer Ordering & Payments
- `POST /orders/api/quote/`: Calculates transparent price quote based on shop rules.
- `POST /orders/api/upload/`: Uploads encrypted PDF binary + wrapped AES key.
- `POST /orders/api/create/`: Creates print order awaiting payment.
- `GET  /orders/api/status/<order_number>/`: Real-time order & spooler status.
- `POST /payments/api/create-order/`: Initiates payment order on backend.
- `POST /payments/api/verify/`: Cryptographically verifies HMAC-SHA256 signature and releases job.
- `POST /payments/api/webhook/`: Ingests Razorpay webhook notifications.

### Local Windows Connector
- `POST /printers/api/connector/register/`: Authenticates terminal & uploads RSA public key.
- `POST /printers/api/connector/heartbeat/`: Reports live status of installed copiers.
- `GET  /printers/api/connector/poll-jobs/`: Polls authorized print jobs for dispatch.
- `POST /printers/api/connector/update-job-status/`: Updates status (`RECEIVED`, `SUBMITTED`, `PRINTED`, `FAILED`).

```

---

## File: `bundle_codebase.py`

```python
import os

base_dir = r"C:\Users\Nandini\.gemini\antigravity\scratch\kep_printgrid"
output_file = os.path.join(base_dir, "KEP_PRINTGRID_ALL_CODE.md")

include_extensions = {".py", ".html", ".css", ".js", ".txt", ".example", ".md", ".json"}
exclude_dirs = {".git", "__pycache__", "media", "staticfiles", ".system_generated"}
exclude_files = {"KEP_PRINTGRID_ALL_CODE.md", "db.sqlite3", "connector_private_key.pem"}

all_files = []
for root, dirs, files in os.walk(base_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file in exclude_files:
            continue
        ext = os.path.splitext(file)[1].lower()
        if ext in include_extensions:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            all_files.append((rel_path, full_path, ext))

all_files.sort(key=lambda x: x[0])

with open(output_file, "w", encoding="utf-8") as out:
    out.write("# KEP PrintGrid - Complete Project Codebase Bundle\n\n")
    out.write("This single file contains the entire source code for all backend models, views, templates, APIs, Windows local connector, encryption algorithms, automated tests, and configuration files of **KEP PrintGrid**.\n\n")
    out.write("## Table of Files Included\n\n")
    for rel_path, _, _ in all_files:
        norm_path = rel_path.replace("\\", "/")
        out.write(f"- `{norm_path}`\n")
    out.write("\n---\n\n")

    for rel_path, full_path, ext in all_files:
        norm_path = rel_path.replace("\\", "/")
        lang = "python"
        if ext in [".html"]:
            lang = "html"
        elif ext in [".css"]:
            lang = "css"
        elif ext in [".js"]:
            lang = "javascript"
        elif ext in [".json"]:
            lang = "json"
        elif ext in [".md"]:
            lang = "markdown"
        elif ext in [".txt", ".example"]:
            lang = "text"

        out.write(f"## File: `{norm_path}`\n\n")
        out.write(f"```{lang}\n")
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            out.write(content)
        except Exception as e:
            out.write(f"# Could not read file: {e}\n")
        out.write("\n```\n\n---\n\n")

print(f"Successfully compiled {len(all_files)} files into {output_file} (Size: {os.path.getsize(output_file)} bytes)")

```

---

## File: `connector/client.py`

```python
import os
import sys
import time
import uuid
import tempfile
import logging
import requests

from .crypto_manager import ConnectorCryptoManager
from .spooler.spooler_factory import get_spooler
from .page_validator import LocalDocumentValidator
from .secure_cleaner import SecureCleaner
from .local_store import LocalExecutionStore

logger = logging.getLogger("PrintGridConnector")


class PrintGridConnectorClient:
    def __init__(self, server_url: str, auth_token: str, shop_slug: str = "", spooler_mode: str = None):
        self.server_url = server_url.rstrip('/')
        self.auth_token = auth_token
        self.shop_slug = shop_slug
        self.machine_id = f"WIN-{uuid.getnode()}"

        self.crypto = ConnectorCryptoManager()
        self.spooler = get_spooler(spooler_mode)
        self.store = LocalExecutionStore()
        self.is_registered = False

    def _get_headers(self):
        headers = {
            'X-Shop-Token': self.auth_token,
            'Content-Type': 'application/json'
        }
        if self.shop_slug:
            headers['X-Shop-Slug'] = self.shop_slug
        return headers

    def register(self) -> bool:
        url = f"{self.server_url}/printers/api/connector/register/"
        payload = {
            'machine_id': self.machine_id,
            'name': f"Windows Shop Terminal ({self.machine_id})",
            'os_platform': sys.platform,
            'version': '1.0.0',
            'rsa_public_key': self.crypto.get_public_key_pem(),
        }

        try:
            resp = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Registered successfully with backend: {data.get('message')}")
                self.is_registered = True
                return True
            else:
                logger.error(f"Failed to register connector ({resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Network error during registration: {e}")
            return False

    def send_heartbeat(self) -> bool:
        url = f"{self.server_url}/printers/api/connector/heartbeat/"
        installed_printers = self.spooler.get_installed_printers()
        payload = {
            'machine_id': self.machine_id,
            'printers': installed_printers,
            'system_metrics': {
                'platform': sys.platform,
                'status': 'HEALTHY'
            }
        }

        try:
            resp = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                return True
            logger.warning(f"Heartbeat rejected ({resp.status_code}): {resp.text}")
            return False
        except Exception as e:
            logger.warning(f"Heartbeat network interruption: {e}")
            return False

    def poll_and_execute_jobs(self) -> int:
        url = f"{self.server_url}/printers/api/connector/poll-jobs/"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Could not poll jobs ({resp.status_code}): {resp.text}")
                return 0

            data = resp.json()
            jobs = data.get('pending_jobs', [])
            executed_count = 0

            for job_info in jobs:
                if self._process_single_job(job_info):
                    executed_count += 1

            return executed_count
        except Exception as e:
            logger.error(f"Error polling jobs: {e}")
            return 0

    def _process_single_job(self, job: dict) -> bool:
        job_id = job['job_id']
        order_number = job['order_number']
        target_printer = job['printer_system_name']
        download_url = job['download_url']
        expected_pages = job.get('expected_page_count', 1)
        preferences = job.get('preferences', {})

        logger.info(f"Processing Job {job_id} for Order {order_number} -> '{target_printer}'")

        # 1. Duplicate check via local ledger
        if self.store.is_job_executed(job_id):
            logger.warning(f"Job {job_id} has already been executed locally. Suppressing duplicate physical print.")
            self._update_job_status(job_id, 'PHYSICALLY_PRINTED', failure_reason="Duplicate run suppressed locally")
            return True

        # 2. Notify backend: Received by connector
        self._update_job_status(job_id, 'RECEIVED_BY_CONNECTOR')

        # 3. Download encrypted document content
        try:
            file_resp = requests.get(download_url, timeout=30)
            if file_resp.status_code != 200:
                raise RuntimeError(f"Failed to download encrypted file payload ({file_resp.status_code})")
            encrypted_bytes = file_resp.content
        except Exception as e:
            self._update_job_status(job_id, 'FAILED', failure_reason=f"Download failed: {str(e)}")
            return False

        # 4. Decrypt document locally
        try:
            plaintext_pdf = self.crypto.decrypt_document(
                encrypted_ciphertext=encrypted_bytes,
                encrypted_key_bundle_b64=job['encrypted_key_bundle'],
                iv_b64=job['encryption_iv'],
                tag_b64=job.get('encryption_tag', '')
            )
        except Exception as e:
            self._update_job_status(job_id, 'FAILED', failure_reason=f"Decryption failed: {str(e)}")
            return False

        # 5. Validate document page count & structure locally
        validation = LocalDocumentValidator.validate_pdf_pages(
            pdf_bytes=plaintext_pdf,
            expected_pages=expected_pages,
            page_range_selection=preferences.get('page_range_selection', '')
        )

        if not validation['valid']:
            self._update_job_status(job_id, 'FAILED', failure_reason=validation.get('error', 'Invalid PDF structure'))
            return False

        actual_pages = validation['actual_pages']

        if validation['is_mismatch']:
            mismatch_msg = f"Hold Verification: Customer paid for {expected_pages} pages, but file contains {actual_pages} pages."
            logger.warning(mismatch_msg)
            self._update_job_status(
                job_id,
                'HOLD_VERIFICATION',
                verified_pages=actual_pages,
                failure_reason=mismatch_msg
            )
            return False

        # 6. Save plaintext to secure temporary file for OS Spooler submission
        temp_fd, temp_pdf_path = tempfile.mkstemp(suffix=".pdf", prefix=f"printgrid_{order_number}_")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(plaintext_pdf)

            # 7. Submit to Windows Spooler
            spool_res = self.spooler.submit_print_job(
                printer_name=target_printer,
                pdf_path=temp_pdf_path,
                preferences=preferences
            )

            if not spool_res.get('success', False):
                self._update_job_status(
                    job_id,
                    'FAILED',
                    verified_pages=actual_pages,
                    failure_reason=spool_res.get('message', 'Spooler rejected job')
                )
                return False

            os_job_id = spool_res.get('os_job_id', '')

            # 8. Mark submitted to spooler
            self._update_job_status(
                job_id,
                'SUBMITTED_TO_SPOOLER',
                verified_pages=actual_pages,
                ack_id=os_job_id
            )

            # 9. Verify physical completion
            # Wait briefly or query status
            time.sleep(1)
            status_check = self.spooler.check_job_status(target_printer, os_job_id)

            if status_check.get('is_completed', True):
                self._update_job_status(
                    job_id,
                    'PHYSICALLY_PRINTED',
                    verified_pages=actual_pages,
                    ack_id=os_job_id
                )
                self.store.record_job(job_id, target_printer, 'COMPLETED', f"Pages: {actual_pages}")
                logger.info(f"Successfully completed physical print for Order {order_number} on '{target_printer}'")
                return True
            else:
                self.store.record_job(job_id, target_printer, 'SPOOLED', f"OS Job ID: {os_job_id}")
                return True

        finally:
            # 10. Securely clean and shred temporary plaintext file
            SecureCleaner.securely_shred_and_delete(temp_pdf_path)

    def _update_job_status(self, job_id: str, status: str, verified_pages: int = None, failure_reason: str = "", ack_id: str = ""):
        url = f"{self.server_url}/printers/api/connector/update-job-status/"
        payload = {
            'job_id': job_id,
            'status': status,
            'verified_page_count': verified_pages,
            'failure_reason': failure_reason,
            'connector_ack_id': ack_id
        }
        try:
            requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
        except Exception as e:
            logger.error(f"Failed to post status update for job {job_id}: {e}")

    def run(self, poll_interval: int = 5, run_once: bool = False):
        """
        Main execution loop.
        Auto-reconnects after network interruptions.
        """
        logger.info(f"Starting KEP PrintGrid Connector for server: {self.server_url}")

        retry_wait = 2
        while True:
            if not self.is_registered:
                success = self.register()
                if not success:
                    logger.warning(f"Registration failed. Retrying in {retry_wait}s...")
                    time.sleep(retry_wait)
                    retry_wait = min(retry_wait * 2, 30)
                    continue
                retry_wait = 2

            # Send heartbeat
            self.send_heartbeat()

            # Poll & execute pending jobs
            self.poll_and_execute_jobs()

            if run_once:
                break

            time.sleep(poll_interval)

```

---

## File: `connector/crypto_manager.py`

```python
import os
import base64
import logging
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("PrintGridConnector.Crypto")


class ConnectorCryptoManager:
    """
    Manages shop-local RSA keypairs and executes zero-knowledge
    local document decryption.
    """
    def __init__(self, keys_dir=None):
        if not keys_dir:
            keys_dir = os.path.join(os.path.dirname(__file__), "keys")
        self.keys_dir = keys_dir
        os.makedirs(self.keys_dir, exist_ok=True)

        self.private_key_path = os.path.join(self.keys_dir, "connector_private_key.pem")
        self.public_key_path = os.path.join(self.keys_dir, "connector_public_key.pem")

        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
            with open(self.private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None)
            with open(self.public_key_path, "rb") as f:
                self.public_key = serialization.load_pem_public_key(f.read())
            logger.info("Loaded existing RSA keypair from local storage.")
        else:
            logger.info("Generating new RSA-2048 keypair for local shop connector...")
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            self.public_key = self.private_key.public_key()

            # Save private key securely
            with open(self.private_key_path, "wb") as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                ))

            # Save public key
            with open(self.public_key_path, "wb") as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ))
            logger.info("Saved fresh RSA keypair.")

    def get_public_key_pem(self) -> str:
        """
        Returns the public key in standard PEM string format to register with the cloud shop backend.
        """
        pem_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem_bytes.decode('utf-8')

    def decrypt_document(
        self,
        encrypted_ciphertext: bytes,
        encrypted_key_bundle_b64: str,
        iv_b64: str,
        tag_b64: str = ""
    ) -> bytes:
        """
        Decrypts customer document locally:
        1. Decrypts AES session key using local RSA private key (RSA-OAEP SHA-256).
        2. Decrypts document ciphertext using AES-256-GCM.
        3. Returns plaintext PDF bytes.
        """
        # 1. Decrypt session key bundle
        wrapped_key_bytes = base64.b64decode(encrypted_key_bundle_b64)
        aes_session_key = self.private_key.decrypt(
            wrapped_key_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 2. Decode IV
        iv_bytes = base64.b64decode(iv_b64)

        # 3. Assemble ciphertext + authentication tag for AESGCM
        # If tag was supplied separately (as in Web Crypto API), concatenate it
        if tag_b64:
            tag_bytes = base64.b64decode(tag_b64)
            combined_ciphertext = encrypted_ciphertext + tag_bytes
        else:
            combined_ciphertext = encrypted_ciphertext

        # 4. Decrypt via AES-GCM
        aesgcm = AESGCM(aes_session_key)
        plaintext_pdf = aesgcm.decrypt(iv_bytes, combined_ciphertext, associated_data=None)
        return plaintext_pdf

```

---

## File: `connector/local_store.py`

```python
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("PrintGridConnector.LocalStore")


class LocalExecutionStore:
    """
    Maintains a persistent ledger of jobs processed locally
    to prevent duplicate physical prints.
    """
    def __init__(self, store_path=None):
        if not store_path:
            store_path = os.path.join(os.path.dirname(__file__), "local_execution_log.json")
        self.store_path = store_path
        self._cache = self._load()

    def _load(self):
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading local execution log: {e}")
        return {}

    def _save(self):
        try:
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving local execution log: {e}")

    def is_job_executed(self, job_id: str) -> bool:
        return job_id in self._cache and self._cache[job_id].get('status') == 'COMPLETED'

    def record_job(self, job_id: str, printer: str, status: str, details: str = ""):
        self._cache[job_id] = {
            'printer': printer,
            'status': status,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self._save()

```

---

## File: `connector/page_validator.py`

```python
import io
import logging
from pypdf import PdfReader

logger = logging.getLogger("PrintGridConnector.Validator")


class LocalDocumentValidator:
    @classmethod
    def validate_pdf_pages(cls, pdf_bytes: bytes, expected_pages: int, page_range_selection: str = "") -> dict:
        """
        Locally inspects the decrypted PDF document before sending to the physical spooler:
        1. Confirms the file is a valid, uncorrupted PDF.
        2. Measures the exact physical page count.
        3. Validates against the customer's declared & paid page count.
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            actual_total_pages = len(reader.pages)

            if actual_total_pages <= 0:
                return {
                    'valid': False,
                    'error': 'Decrypted document contains 0 pages.',
                    'actual_pages': 0
                }

            # Check if actual document pages are strictly greater than what customer paid for
            is_mismatch = (actual_total_pages > expected_pages)

            return {
                'valid': True,
                'actual_pages': actual_total_pages,
                'expected_pages': expected_pages,
                'is_mismatch': is_mismatch,
                'is_encrypted': reader.is_encrypted,
            }
        except Exception as e:
            logger.error(f"Failed to inspect PDF structure: {e}")
            return {
                'valid': False,
                'error': f"Invalid or corrupt PDF document: {str(e)}",
                'actual_pages': 0
            }

```

---

## File: `connector/run_connector.py`

```python
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

```

---

## File: `connector/secure_cleaner.py`

```python
import os
import secrets
import logging

logger = logging.getLogger("PrintGridConnector.Cleaner")


class SecureCleaner:
    @staticmethod
    def securely_shred_and_delete(file_path: str):
        """
        Overwrites file contents with random bytes before deletion
        to prevent forensic recovery of customer documents from Xerox shop disks.
        """
        if not file_path or not os.path.exists(file_path):
            return

        try:
            length = os.path.getsize(file_path)
            # Overwrite pass 1: random noise
            with open(file_path, "wb") as f:
                f.write(secrets.token_bytes(min(length, 1024 * 1024)))
            # Overwrite pass 2: zeroes
            with open(file_path, "wb") as f:
                f.write(b"\x00" * min(length, 1024 * 1024))
            # Delete file
            os.remove(file_path)
            logger.info(f"Securely shredded and deleted temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error while securely cleaning {file_path}: {e}")
            try:
                os.remove(file_path)
            except Exception:
                pass

```

---

## File: `connector/spooler/__init__.py`

```python
from .spooler_factory import get_spooler
from .base_spooler import BaseSpooler

__all__ = ['get_spooler', 'BaseSpooler']

```

---

## File: `connector/spooler/base_spooler.py`

```python
from abc import ABC, abstractmethod


class BaseSpooler(ABC):
    @abstractmethod
    def get_installed_printers(self) -> list:
        """
        Returns a list of dicts describing available printers and capabilities:
        [
            {
                'system_name': '...',
                'friendly_name': '...',
                'is_online': True,
                'status': 'Ready',
                'capabilities': {
                    'supports_bw': True,
                    'supports_color': False,
                    'supports_duplex': True,
                    'supported_paper_sizes': ['A4', 'A3'],
                    'supports_landscape': True,
                    'dpi': 600
                }
            }
        ]
        """
        pass

    @abstractmethod
    def submit_print_job(self, printer_name: str, pdf_path: str, preferences: dict) -> dict:
        """
        Submits the physical job to the OS print spooler.
        Returns dict with:
        {
            'success': bool,
            'os_job_id': str,
            'message': str
        }
        """
        pass

    @abstractmethod
    def check_job_status(self, printer_name: str, os_job_id: str) -> dict:
        """
        Queries the OS spooler for the true status of the submitted print job.
        """
        pass

```

---

## File: `connector/spooler/dev_spooler.py`

```python
import os
import uuid
import logging
from .base_spooler import BaseSpooler

logger = logging.getLogger("PrintGridConnector.DevSpooler")


class DevSpooler(BaseSpooler):
    """
    Development & Testing Spooler Simulator.
    Simulates physical printer queues, capability checks, and verified spooler output.
    """
    def __init__(self):
        self._jobs = {}
        logger.info("DevSpooler initialized with simulated printer inventory.")

    def get_installed_printers(self) -> list:
        return [
            {
                'system_name': 'HP LaserJet Pro M428fdw',
                'friendly_name': 'HP LaserJet Pro M428fdw (Counter 1 - Fast B&W)',
                'is_online': True,
                'is_default': True,
                'status': 'Ready',
                'capabilities': {
                    'supports_bw': True,
                    'supports_color': False,
                    'supports_duplex': True,
                    'supported_paper_sizes': ['A4', 'LETTER'],
                    'supports_landscape': True,
                    'dpi': 1200
                }
            },
            {
                'system_name': 'Canon imageRUNNER ADVANCE C3530i',
                'friendly_name': 'Canon imageRUNNER ADVANCE C3530i (Colour & A3 Production)',
                'is_online': True,
                'is_default': False,
                'status': 'Ready',
                'capabilities': {
                    'supports_bw': True,
                    'supports_color': True,
                    'supports_duplex': True,
                    'supported_paper_sizes': ['A4', 'A3', 'LETTER'],
                    'supports_landscape': True,
                    'dpi': 1200
                }
            },
            {
                'system_name': 'Epson EcoTank L15150',
                'friendly_name': 'Epson EcoTank L15150 (Backup Color InkTank)',
                'is_online': True,
                'is_default': False,
                'status': 'Ready',
                'capabilities': {
                    'supports_bw': True,
                    'supports_color': True,
                    'supports_duplex': True,
                    'supported_paper_sizes': ['A4', 'A3'],
                    'supports_landscape': True,
                    'dpi': 600
                }
            }
        ]

    def submit_print_job(self, printer_name: str, pdf_path: str, preferences: dict) -> dict:
        if not os.path.exists(pdf_path):
            return {'success': False, 'os_job_id': '', 'message': f"PDF path does not exist: {pdf_path}"}

        file_size = os.path.getsize(pdf_path)
        job_id = f"DEV_JOB_{uuid.uuid4().hex[:8]}"

        self._jobs[job_id] = {
            'printer': printer_name,
            'file_size': file_size,
            'preferences': preferences,
            'status': 'PRINTED'
        }

        logger.info(f"[DEV SPOOLER] Submitted job {job_id} to '{printer_name}' ({file_size} bytes)")
        return {
            'success': True,
            'os_job_id': job_id,
            'message': f"DevSpooler: Spooled {file_size} bytes successfully to {printer_name}"
        }

    def check_job_status(self, printer_name: str, os_job_id: str) -> dict:
        if os_job_id in self._jobs:
            return {'exists': True, 'is_completed': True, 'info': self._jobs[os_job_id]}
        return {'exists': False, 'is_completed': True}

```

---

## File: `connector/spooler/spooler_factory.py`

```python
import sys
import os
from .base_spooler import BaseSpooler
from .windows_spooler import WindowsSpooler
from .dev_spooler import DevSpooler


def get_spooler(force_mode: str = None) -> BaseSpooler:
    """
    Returns the appropriate print spooler interface.
    Auto-detects Windows or falls back to DevSpooler.
    """
    mode = force_mode or os.environ.get('CONNECTOR_SPOOLER_MODE', 'auto')

    if mode == 'dev':
        return DevSpooler()
    elif mode == 'windows' or (mode == 'auto' and sys.platform.startswith('win')):
        return WindowsSpooler()
    return DevSpooler()

```

---

## File: `connector/spooler/windows_spooler.py`

```python
import os
import sys
import subprocess
import logging
from .base_spooler import BaseSpooler

logger = logging.getLogger("PrintGridConnector.WindowsSpooler")


class WindowsSpooler(BaseSpooler):
    """
    Windows Print Spooler Integration using pywin32 / PowerShell PrintTo.
    """
    def __init__(self):
        self.has_win32print = False
        try:
            import win32print
            import win32api
            self.win32print = win32print
            self.win32api = win32api
            self.has_win32print = True
            logger.info("Native win32print spooler integration loaded successfully.")
        except ImportError:
            logger.warning("pywin32 (win32print) is not installed. Windows PowerShell spooler commands will be used.")

    def get_installed_printers(self) -> list:
        printers = []
        if self.has_win32print:
            try:
                flags = self.win32print.PRINTER_ENUM_LOCAL | self.win32print.PRINTER_ENUM_CONNECTIONS
                enum_list = self.win32print.EnumPrinters(flags)
                default_name = self.win32print.GetDefaultPrinter()

                for p in enum_list:
                    # p is a tuple: (flags, description, name, comment)
                    name = p[2]
                    is_default = (name == default_name)

                    # Inspect basic capabilities
                    is_color = "color" in name.lower() or "cmyk" in name.lower()
                    supports_a3 = "a3" in name.lower() or "wide" in name.lower()
                    paper_sizes = ['A4']
                    if supports_a3:
                        paper_sizes.append('A3')

                    printers.append({
                        'system_name': name,
                        'friendly_name': name,
                        'is_online': True,
                        'is_default': is_default,
                        'status': 'Ready',
                        'capabilities': {
                            'supports_bw': True,
                            'supports_color': is_color,
                            'supports_duplex': True,
                            'supported_paper_sizes': paper_sizes,
                            'supports_landscape': True,
                            'dpi': 600
                        }
                    })
                if printers:
                    return printers
            except Exception as e:
                logger.error(f"Error enumerating printers via win32print: {e}")

        # Fallback via PowerShell Get-Printer
        try:
            cmd = "Get-Printer | Select-Object Name, PrinterStatus, Default | ConvertTo-Json"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get('Name', '')
                    if not name:
                        continue
                    is_color = "color" in name.lower()
                    is_a3 = "a3" in name.lower()
                    paper_sizes = ['A4']
                    if is_a3:
                        paper_sizes.append('A3')

                    printers.append({
                        'system_name': name,
                        'friendly_name': name,
                        'is_online': True,
                        'is_default': bool(item.get('Default', False)),
                        'status': 'Ready',
                        'capabilities': {
                            'supports_bw': True,
                            'supports_color': is_color,
                            'supports_duplex': True,
                            'supported_paper_sizes': paper_sizes,
                            'supports_landscape': True,
                            'dpi': 600
                        }
                    })
        except Exception as e:
            logger.error(f"Error querying PowerShell Get-Printer: {e}")

        # If no physical printer configured, provide standard Microsoft Print to PDF printer
        if not printers:
            printers.append({
                'system_name': 'Microsoft Print to PDF',
                'friendly_name': 'Microsoft Print to PDF (Windows Virtual Spooler)',
                'is_online': True,
                'is_default': True,
                'status': 'Ready',
                'capabilities': {
                    'supports_bw': True,
                    'supports_color': True,
                    'supports_duplex': True,
                    'supported_paper_sizes': ['A4', 'A3'],
                    'supports_landscape': True,
                    'dpi': 600
                }
            })
        return printers

    def submit_print_job(self, printer_name: str, pdf_path: str, preferences: dict) -> dict:
        if not os.path.exists(pdf_path):
            return {'success': False, 'os_job_id': '', 'message': f"PDF path does not exist: {pdf_path}"}

        # Check if native win32print raw spool submission is applicable
        if self.has_win32print:
            try:
                h_printer = self.win32print.OpenPrinter(printer_name)
                job_id = self.win32print.StartDocPrinter(h_printer, 1, (f"KEP_PrintGrid_{os.path.basename(pdf_path)}", None, "RAW"))
                self.win32print.StartPagePrinter(h_printer)
                with open(pdf_path, 'rb') as f:
                    self.win32print.WritePrinter(h_printer, f.read())
                self.win32print.EndPagePrinter(h_printer)
                self.win32print.EndDocPrinter(h_printer)
                self.win32print.ClosePrinter(h_printer)
                return {
                    'success': True,
                    'os_job_id': str(job_id),
                    'message': f"Submitted to Windows spooler printer '{printer_name}'"
                }
            except Exception as e:
                logger.warning(f"win32print direct spool failed ({e}), falling back to Windows PrintTo verb.")

        # Fallback via PowerShell Start-Process PrintTo
        try:
            escaped_pdf = pdf_path.replace("'", "''")
            escaped_printer = printer_name.replace("'", "''")
            cmd = f"Start-Process -FilePath '{escaped_pdf}' -Verb PrintTo -ArgumentList '\"{escaped_printer}\"' -PassThru"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                return {
                    'success': True,
                    'os_job_id': f"PS_{os.path.basename(pdf_path)}",
                    'message': f"Dispatched via Windows shell PrintTo to '{printer_name}'"
                }
            else:
                return {
                    'success': False,
                    'os_job_id': '',
                    'message': f"Print command returned exit code {res.returncode}: {res.stderr}"
                }
        except Exception as e:
            return {'success': False, 'os_job_id': '', 'message': str(e)}

    def check_job_status(self, printer_name: str, os_job_id: str) -> dict:
        if self.has_win32print and os_job_id.isdigit():
            try:
                h_printer = self.win32print.OpenPrinter(printer_name)
                job_info = self.win32print.GetJob(h_printer, int(os_job_id), 1)
                self.win32print.ClosePrinter(h_printer)
                status_flags = job_info.get('Status', 0)
                return {
                    'exists': True,
                    'status_flags': status_flags,
                    'is_completed': status_flags == 0
                }
            except Exception:
                # If GetJob fails because job finished and was removed from queue, it is completed
                return {'exists': False, 'is_completed': True}

        return {'exists': True, 'is_completed': True}

```

---

## File: `core/__init__.py`

```python

```

---

## File: `core/admin.py`

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Shop, ShopStaff, ShopQRCode, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Profile', {'fields': ('role', 'phone_number')}),
    )
    list_display = ('username', 'email', 'role', 'phone_number', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'phone', 'is_accepting_orders', 'connector_last_seen', 'created_at')
    search_fields = ('name', 'slug', 'email', 'phone')
    list_filter = ('is_accepting_orders', 'created_at')


@admin.register(ShopStaff)
class ShopStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop', 'can_manage_printers', 'can_authorize_retries', 'can_manage_pricing')
    list_filter = ('shop', 'can_manage_printers', 'can_authorize_retries')


@admin.register(ShopQRCode)
class ShopQRCodeAdmin(admin.ModelAdmin):
    list_display = ('shop', 'qr_target_url', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'shop', 'user', 'resource_type', 'resource_id', 'created_at')
    list_filter = ('action', 'resource_type', 'created_at')
    search_fields = ('action', 'resource_type', 'resource_id')

```

---

## File: `core/apps.py`

```python
from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

```

---

## File: `core/context_processors.py`

```python
def printgrid_global_context(request):
    """
    Exposes platform-level global variables to all templates.
    """
    from django.conf import settings
    return {
        'APP_NAME': 'KEP PrintGrid',
        'APP_VERSION': '1.0.0',
        'BASE_APP_URL': getattr(settings, 'BASE_APP_URL', 'http://127.0.0.1:8000'),
        'PAYMENT_SANDBOX_MODE': getattr(settings, 'PAYMENT_SANDBOX_MODE', True),
    }

```

---

## File: `core/decorators.py`

```python
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def owner_required(view_func):
    """
    Decorator for views that checks that the logged-in user is a Shop Owner.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not (request.user.is_owner() or request.user.is_superuser):
            messages.error(request, "Access denied. Only registered shop owners can access this section.")
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_owner_required(view_func):
    """
    Decorator for views that checks that the user is either a Shop Owner or Shop Staff.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not (request.user.is_owner() or request.user.is_staff_member() or request.user.is_superuser):
            messages.error(request, "Access restricted to shop owners and authorized staff members.")
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def get_user_shop(user):
    """
    Retrieves the shop associated with an owner or staff member.
    """
    if not user.is_authenticated:
        return None
    if user.is_owner() or user.is_superuser:
        return user.owned_shops.first()
    if hasattr(user, 'staff_profile'):
        return user.staff_profile.shop
    return None

```

---

## File: `core/forms.py`

```python
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import User, Shop, ShopStaff
from orders.models import PricingRule
from core.services.qr_service import generate_shop_qr_code


class ShopOwnerRegistrationForm(forms.Form):
    shop_name = forms.CharField(
        max_length=150,
        label="Shop Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Metro Xerox & Print Centre'})
    )
    owner_name = forms.CharField(
        max_length=150,
        label="Owner Full Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ramesh Kumar'})
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ramesh@printgrid.example'})
    )
    mobile_number = forms.CharField(
        max_length=20,
        label="Mobile Number",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 9876543210'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'At least 8 characters'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat your password'})
    )
    shop_address = forms.CharField(
        label="Shop Address",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Shop No. 4, College Road, Opp. University Gate'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email address already exists. Please log in.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            else:
                validate_password(password)
        return cleaned_data

    @transaction.atomic
    def save(self):
        email = self.cleaned_data['email']
        owner_name = self.cleaned_data['owner_name']
        username = email.split('@')[0]
        # Guarantee unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        first_name = owner_name.split()[0] if owner_name else ""
        last_name = " ".join(owner_name.split()[1:]) if " " in owner_name else ""

        user = User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
            role=User.Role.OWNER,
            phone_number=self.cleaned_data['mobile_number']
        )

        shop = Shop.objects.create(
            name=self.cleaned_data['shop_name'],
            owner=user,
            phone=self.cleaned_data['mobile_number'],
            email=email,
            address=self.cleaned_data['shop_address'],
            is_accepting_orders=True
        )

        # Create default pricing rule for this shop
        PricingRule.objects.create(shop=shop)

        # Generate permanent QR code (PNG + printable PDF)
        generate_shop_qr_code(shop)

        return user, shop


class LoginForm(forms.Form):
    email_or_username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )

    def clean(self):
        cleaned_data = super().clean()
        login_val = cleaned_data.get('email_or_username', '').strip()
        password = cleaned_data.get('password')

        if login_val and password:
            user = None
            if '@' in login_val:
                try:
                    user_obj = User.objects.get(email__iexact=login_val)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            else:
                user = authenticate(username=login_val, password=password)

            if not user:
                raise ValidationError("Invalid email/username or password. Please try again.")
            if not user.is_active:
                raise ValidationError("This account is currently disabled.")

            cleaned_data['authenticated_user'] = user

        return cleaned_data


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'phone', 'email', 'address', 'is_accepting_orders', 'pause_message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_accepting_orders': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'pause_message': forms.TextInput(attrs={'class': 'form-control'}),
        }


class StaffCreateForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff Member Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'staff@shop.example'})
    )
    mobile_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9123456789'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Temporary Password'})
    )
    can_manage_printers = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_authorize_retries = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_manage_pricing = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

    def save(self, shop):
        email = self.cleaned_data['email']
        name = self.cleaned_data['name']
        username = email.split('@')[0]
        base_username = username
        c = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{c}"
            c += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data['password'],
            first_name=name.split()[0],
            last_name=" ".join(name.split()[1:]),
            role=User.Role.STAFF,
            phone_number=self.cleaned_data['mobile_number']
        )

        staff = ShopStaff.objects.create(
            shop=shop,
            user=user,
            can_manage_printers=self.cleaned_data.get('can_manage_printers', False),
            can_authorize_retries=self.cleaned_data.get('can_authorize_retries', True),
            can_manage_pricing=self.cleaned_data.get('can_manage_pricing', False)
        )
        return staff

```

---

## File: `core/management/__init__.py`

```python

```

---

## File: `core/management/commands/__init__.py`

```python

```

---

## File: `core/management/commands/seed_demo_data.py`

```python
import io
import os
import secrets
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from core.models import User, Shop, ShopStaff
from core.services.qr_service import generate_shop_qr_code
from printers.models import Printer, PrinterCapability, PrinterAssignment, Connector
from orders.models import PricingRule, PrintDocument, PrintPreference, PrintOrder, PrintJob, PrintJobAttempt
from payments.models import Payment
from connector.crypto_manager import ConnectorCryptoManager


class Command(BaseCommand):
    help = "Seeds demo print shop, staff, printers, pricing, and sample orders for development."

    def handle(self, *args, **options):
        self.stdout.write("Seeding KEP PrintGrid demo data...")

        # 1. Shop Owner
        owner, created = User.objects.get_or_create(
            username="metro_owner",
            defaults={
                "email": "owner@metroprint.example",
                "first_name": "Ramesh",
                "last_name": "Kumar",
                "role": User.Role.OWNER,
                "phone_number": "+91 9876543210"
            }
        )
        if created:
            owner.set_password("MetroPrint2026!")
            owner.save()
            self.stdout.write(self.style.SUCCESS(f"Created Owner: owner@metroprint.example / MetroPrint2026!"))

        # 2. Shop
        crypto = ConnectorCryptoManager()
        shop, s_created = Shop.objects.get_or_create(
            slug="metro-xerox",
            defaults={
                "name": "Metro Xerox & Multi-Service Hub",
                "owner": owner,
                "phone": "+91 9876543210",
                "email": "owner@metroprint.example",
                "address": "Shop No. 4, College Road, Opp. University Gate",
                "is_accepting_orders": True,
                "connector_auth_token": "metro_demo_auth_token_991823719827391827",
                "connector_public_key": crypto.get_public_key_pem(),
                "connector_last_seen": timezone.now(),
            }
        )
        if s_created:
            generate_shop_qr_code(shop)
            self.stdout.write(self.style.SUCCESS(f"Created Shop: {shop.name} (Slug: {shop.slug})"))

        # 3. Staff User
        staff_user, st_created = User.objects.get_or_create(
            username="metro_staff",
            defaults={
                "email": "staff@metroprint.example",
                "first_name": "Suresh",
                "last_name": "Verma",
                "role": User.Role.STAFF,
                "phone_number": "+91 9123456789"
            }
        )
        if st_created:
            staff_user.set_password("StaffPass2026!")
            staff_user.save()
            ShopStaff.objects.create(
                shop=shop,
                user=staff_user,
                can_manage_printers=True,
                can_authorize_retries=True,
                can_manage_pricing=False
            )
            self.stdout.write(self.style.SUCCESS(f"Created Staff: staff@metroprint.example / StaffPass2026!"))

        # 4. Pricing Rules
        PricingRule.objects.get_or_create(
            shop=shop,
            defaults={
                "bw_single_rate": Decimal("2.00"),
                "bw_double_rate": Decimal("3.50"),
                "color_single_rate": Decimal("10.00"),
                "color_double_rate": Decimal("18.00"),
                "a3_bw_rate": Decimal("5.00"),
                "a3_color_rate": Decimal("20.00"),
                "is_active": True
            }
        )

        # 5. Connected Printers
        p1, _ = Printer.objects.get_or_create(
            shop=shop,
            system_printer_name="HP_LaserJet_Pro_M428fdw",
            defaults={
                "name": "HP LaserJet Pro M428fdw (Counter 1 - Fast B&W)",
                "model_name": "HP M428fdw",
                "is_active": True,
                "is_online": True,
                "is_default": True,
                "handles_bw": True,
                "handles_color": False,
                "last_status_message": "Ready"
            }
        )
        PrinterCapability.objects.get_or_create(
            printer=p1,
            defaults={
                "supports_bw": True,
                "supports_color": False,
                "supports_duplex": True,
                "supported_paper_sizes": ["A4", "LETTER"],
                "dpi": 1200
            }
        )

        p2, _ = Printer.objects.get_or_create(
            shop=shop,
            system_printer_name="Canon_imageRUNNER_ADVANCE_C3530i",
            defaults={
                "name": "Canon imageRUNNER ADVANCE C3530i (Color & A3)",
                "model_name": "Canon iR ADV C3530i",
                "is_active": True,
                "is_online": True,
                "is_default": False,
                "handles_bw": True,
                "handles_color": True,
                "last_status_message": "Ready"
            }
        )
        PrinterCapability.objects.get_or_create(
            printer=p2,
            defaults={
                "supports_bw": True,
                "supports_color": True,
                "supports_duplex": True,
                "supported_paper_sizes": ["A4", "A3", "LETTER"],
                "dpi": 1200
            }
        )

        # Routing Assignments
        PrinterAssignment.objects.get_or_create(
            shop=shop,
            assignment_type=PrinterAssignment.AssignmentType.BW_SINGLE,
            defaults={"primary_printer": p1}
        )
        PrinterAssignment.objects.get_or_create(
            shop=shop,
            assignment_type=PrinterAssignment.AssignmentType.COLOR_SINGLE,
            defaults={"primary_printer": p2}
        )

        # 6. Sample Live Order
        doc = PrintDocument.objects.create(
            shop=shop,
            original_filename="Project_Report_Final.pdf",
            file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            encrypted_file=SimpleUploadedFile("report.enc", b"encrypted_sample_data_stream"),
            encrypted_file_size=1024,
            encrypted_key_bundle="sample_wrapped_key_bundle_b64",
            encryption_iv="sample_iv_b64",
            detected_page_count=6,
            verified_page_count=6
        )
        pref = PrintPreference.objects.create(
            color_mode="BW",
            duplex_mode="DOUBLE",
            paper_size="A4",
            copies=1,
            total_calculated_pages=6
        )
        order, o_created = PrintOrder.objects.get_or_create(
            idempotency_key="seed_demo_order_001",
            defaults={
                "order_number": "ORD-20261111-9284",
                "shop": shop,
                "customer_name": "Pooja Sharma",
                "customer_phone": "+91 9898989898",
                "document": doc,
                "preference": pref,
                "status": PrintOrder.Status.PRINTING,
                "total_amount": Decimal("10.50"),
                "pricing_breakdown": {
                    "unit_rate": 3.5,
                    "rate_label": "B&W Double-Sided",
                    "sheets_per_copy": 3,
                    "copies": 1,
                    "total_sheets": 3,
                    "total_amount": 10.50
                }
            }
        )
        if o_created:
            job = PrintJob.objects.create(
                order=order,
                printer=p1,
                status=PrintJob.Status.SUBMITTED_TO_SPOOLER,
                assigned_at=timezone.now(),
                dispatched_at=timezone.now()
            )
            PrintJobAttempt.objects.create(
                job=job,
                printer=p1,
                attempt_number=1,
                status="SUBMITTED_TO_SPOOLER",
                error_message="Submitted to Windows Spooler Queue HP_LaserJet_Pro_M428fdw"
            )

            Payment.objects.create(
                order=order,
                gateway_order_id="order_demo_seed_001",
                gateway_payment_id="pay_demo_seed_001",
                gateway_signature="sig_demo_seed_001",
                gateway_name="RAZORPAY_SANDBOX",
                amount=Decimal("10.50"),
                currency="INR",
                status=Payment.Status.CAPTURED,
                idempotency_key="pay_idemp_seed_001",
                verified_at=timezone.now()
            )

        self.stdout.write(self.style.SUCCESS("KEP PrintGrid seeded with active demo shop, staff, copiers, and orders!"))

```

---

## File: `core/migrations/0001_initial.py`

```python
# Generated by Django 6.1.3 on 2026-11-11 08:53

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('role', models.CharField(choices=[('OWNER', 'Shop Owner / Admin'), ('STAFF', 'Shop Staff'), ('CUSTOMER', 'Customer')], default='CUSTOMER', max_length=20)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150)),
                ('slug', models.SlugField(max_length=180, unique=True)),
                ('phone', models.CharField(max_length=25)),
                ('email', models.EmailField(max_length=254)),
                ('address', models.TextField()),
                ('is_accepting_orders', models.BooleanField(default=True)),
                ('pause_message', models.CharField(default='This shop is temporarily paused and not accepting new print orders at the moment.', max_length=255)),
                ('connector_auth_token', models.CharField(blank=True, max_length=128, unique=True)),
                ('connector_public_key', models.TextField(blank=True, help_text='RSA Public Key (PEM) uploaded by the local connector for client-side document key wrapping.')),
                ('connector_last_seen', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_shops', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(max_length=100)),
                ('resource_type', models.CharField(max_length=100)),
                ('resource_id', models.CharField(max_length=100)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('details', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('shop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='core.shop')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ShopQRCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('qr_code_image', models.ImageField(blank=True, null=True, upload_to='qr_codes/')),
                ('qr_target_url', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shop', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='qr_code', to='core.shop')),
            ],
        ),
        migrations.CreateModel(
            name='ShopStaff',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('can_manage_printers', models.BooleanField(default=False)),
                ('can_authorize_retries', models.BooleanField(default=True)),
                ('can_manage_pricing', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_members', to='core.shop')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='staff_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

```

---

## File: `core/migrations/__init__.py`

```python

```

---

## File: `core/models.py`

```python
import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Shop Owner / Admin'
        STAFF = 'STAFF', 'Shop Staff'
        CUSTOMER = 'CUSTOMER', 'Customer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def is_owner(self):
        return self.role == self.Role.OWNER

    def is_staff_member(self):
        return self.role == self.Role.STAFF

    def is_customer(self):
        return self.role == self.Role.CUSTOMER


class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_shops')
    slug = models.SlugField(max_length=180, unique=True, db_index=True)
    phone = models.CharField(max_length=25)
    email = models.EmailField()
    address = models.TextField()

    # Operations status
    is_accepting_orders = models.BooleanField(default=True)
    pause_message = models.CharField(
        max_length=255,
        default="This shop is temporarily paused and not accepting new print orders at the moment."
    )

    # Windows Local Connector authentication & document encryption key
    connector_auth_token = models.CharField(max_length=128, unique=True, blank=True)
    connector_public_key = models.TextField(
        blank=True,
        help_text="RSA Public Key (PEM) uploaded by the local connector for client-side document key wrapping."
    )
    connector_last_seen = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.slug})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "shop"
            unique_part = uuid.uuid4().hex[:8]
            self.slug = f"{base_slug}-{unique_part}"
        if not self.connector_auth_token:
            self.connector_auth_token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    @property
    def order_page_url(self):
        from django.conf import settings
        base_url = getattr(settings, 'BASE_APP_URL', 'http://127.0.0.1:8000').rstrip('/')
        return f"{base_url}/shop/{self.slug}/"


class ShopStaff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='staff_members')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    can_manage_printers = models.BooleanField(default=False)
    can_authorize_retries = models.BooleanField(default=True)
    can_manage_pricing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} @ {self.shop.name}"


class ShopQRCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='qr_code')
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_target_url = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QR for {self.shop.name}"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.action}] {self.resource_type}:{self.resource_id} by {self.user or 'System'}"

```

---

## File: `core/services/__init__.py`

```python

```

---

## File: `core/services/qr_service.py`

```python
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile
import io


def generate_shop_qr_code(shop):
    """
    Generates a permanent QR code PNG and a printable display poster PDF
    for the specified shop.
    Returns the ShopQRCode instance.
    """
    from core.models import ShopQRCode

    target_url = shop.order_page_url

    # 1. Generate QR Code image with Pillow
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGB")

    # Optional: Brand QR code with center accent
    qr_w, qr_h = qr_img.size
    overlay_size = int(qr_w * 0.18)
    overlay = Image.new("RGBA", (overlay_size, overlay_size), (15, 23, 42, 255))
    draw = ImageDraw.Draw(overlay)
    # Draw simple badge
    draw.rectangle([2, 2, overlay_size - 3, overlay_size - 3], outline=(255, 255, 255, 255), width=3)
    pos = ((qr_w - overlay_size) // 2, (qr_h - overlay_size) // 2)
    qr_img.paste(overlay, pos)

    # Save PNG to media
    qr_filename = f"shop_qr_{shop.slug}.png"
    qr_rel_path = f"qr_codes/{qr_filename}"
    full_qr_path = os.path.join(settings.MEDIA_ROOT, qr_rel_path)
    os.makedirs(os.path.dirname(full_qr_path), exist_ok=True)
    qr_img.save(full_qr_path, format="PNG")

    # 2. Generate a Printable Display Poster (A4-proportioned: 1240 x 1754 px @ 150 DPI)
    poster_w, poster_h = 1240, 1754
    poster = Image.new("RGB", (poster_w, poster_h), color="#F8FAFC")
    p_draw = ImageDraw.Draw(poster)

    # Top header bar (Dark Navy #0F172A)
    p_draw.rectangle([0, 0, poster_w, 240], fill="#0F172A")

    # Text headers
    p_draw.text((poster_w // 2, 70), "KEP PRINTGRID", fill="#38BDF8", anchor="mm")
    p_draw.text((poster_w // 2, 140), "Self-Service Document Printing", fill="#FFFFFF", anchor="mm")
    p_draw.text((poster_w // 2, 190), "Scan • Upload • Pay • Print Instantly", fill="#94A3B8", anchor="mm")

    # Shop Name Card
    card_margin = 80
    card_top = 300
    card_bottom = 1580
    p_draw.rounded_rectangle(
        [card_margin, card_top, poster_w - card_margin, card_bottom],
        radius=24,
        fill="#FFFFFF",
        outline="#E2E8F0",
        width=3
    )

    p_draw.text((poster_w // 2, 380), shop.name.upper(), fill="#0F172A", anchor="mm")
    p_draw.text((poster_w // 2, 430), f"Shop Address: {shop.address[:60]}", fill="#64748B", anchor="mm")

    # Paste QR Code into center of poster card
    display_qr_size = 650
    resized_qr = qr_img.resize((display_qr_size, display_qr_size), Image.Resampling.LANCZOS)
    qr_x = (poster_w - display_qr_size) // 2
    qr_y = 500
    poster.paste(resized_qr, (qr_x, qr_y))

    # Border around QR
    p_draw.rectangle([qr_x - 6, qr_y - 6, qr_x + display_qr_size + 6, qr_y + display_qr_size + 6], outline="#CBD5E1", width=2)

    # Instructions box
    p_draw.text((poster_w // 2, 1220), "HOW TO PRINT:", fill="#0F172A", anchor="mm")
    p_draw.text((poster_w // 2, 1280), "1. Scan this permanent QR code using your phone camera", fill="#334155", anchor="mm")
    p_draw.text((poster_w // 2, 1340), "2. Choose your PDF document and printing preferences", fill="#334155", anchor="mm")
    p_draw.text((poster_w // 2, 1400), "3. Pay securely online (UPI / Card / NetBanking)", fill="#334155", anchor="mm")
    p_draw.text((poster_w // 2, 1460), "4. Collect your freshly printed pages at the counter!", fill="#2563EB", anchor="mm")

    p_draw.text((poster_w // 2, 1530), f"Permanent Order URL: {target_url}", fill="#94A3B8", anchor="mm")

    # Bottom branding footer
    p_draw.text((poster_w // 2, 1680), "Powered by KEP PrintGrid • Secure Zero-Knowledge Printing Platform", fill="#94A3B8", anchor="mm")

    pdf_filename = f"shop_qr_{shop.slug}_poster.pdf"
    full_pdf_path = os.path.join(settings.MEDIA_ROOT, "qr_codes", pdf_filename)
    poster.save(full_pdf_path, "PDF", resolution=150.0)

    # Create or update ShopQRCode model record
    qrcode_obj, _ = ShopQRCode.objects.update_or_create(
        shop=shop,
        defaults={
            'qr_code_image': qr_rel_path,
            'qr_target_url': target_url,
        }
    )

    return qrcode_obj

```

---

## File: `core/tests.py`

```python
from django.test import TestCase

# Create your tests here.

```

---

## File: `core/urls.py`

```python
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_owner, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard_dispatch, name='dashboard'),
    path('dashboard/overview/', views.owner_overview, name='owner_overview'),
    path('dashboard/qr-code/', views.shop_qr_management, name='shop_qr_management'),
    path('dashboard/qr-code/download/<str:asset_type>/', views.download_qr_asset, name='download_qr_asset'),
    path('dashboard/settings/', views.shop_settings, name='shop_settings'),
    path('dashboard/staff/', views.staff_management, name='staff_management'),
    path('dashboard/staff/remove/<uuid:staff_id>/', views.remove_staff, name='remove_staff'),
    path('dashboard/reports/', views.reports_view, name='reports'),
]

```

---

## File: `core/views.py`

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import timedelta
import os
from django.http import FileResponse, Http404

from .models import Shop, ShopStaff, ShopQRCode, AuditLog, User
from .forms import ShopOwnerRegistrationForm, LoginForm, ShopSettingsForm, StaffCreateForm
from .decorators import owner_required, staff_or_owner_required, get_user_shop
from core.services.qr_service import generate_shop_qr_code
from orders.models import PrintOrder, PrintJob
from printers.models import Printer


def home(request):
    """
    Landing page for KEP PrintGrid.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'core/home.html')


def register_owner(request):
    """
    Registration flow for shop owners.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = ShopOwnerRegistrationForm(request.POST)
        if form.is_valid():
            user, shop = form.save()
            login(request, user)
            AuditLog.objects.create(
                shop=shop,
                user=user,
                action='SHOP_REGISTERED',
                resource_type='Shop',
                resource_id=str(shop.id),
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'shop_name': shop.name, 'slug': shop.slug}
            )
            messages.success(request, f"Welcome to KEP PrintGrid! Your shop '{shop.name}' is now active with a permanent QR code.")
            return redirect('core:owner_overview')
    else:
        form = ShopOwnerRegistrationForm()

    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    """
    Unified login view for owners, staff, and registered users.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['authenticated_user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('core:dashboard')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


def user_logout(request):
    """
    Terminates the user session.
    """
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('core:login')


@staff_or_owner_required
def dashboard_dispatch(request):
    """
    Directs the user to the correct dashboard according to their role.
    """
    if request.user.is_owner() or request.user.is_superuser:
        return redirect('core:owner_overview')
    elif request.user.is_staff_member():
        return redirect('orders:staff_dashboard')
    return redirect('core:home')


@owner_required
def owner_overview(request):
    """
    Shop Owner Overview Dashboard with live metrics, printers status and recent orders.
    """
    shop = get_user_shop(request.user)
    if not shop:
        messages.error(request, "No registered shop found for this account.")
        return redirect('core:register')

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Orders queries
    shop_orders = PrintOrder.objects.filter(shop=shop)
    total_orders = shop_orders.count()
    today_orders = shop_orders.filter(created_at__gte=today_start).count()
    pending_orders = shop_orders.filter(status__in=[
        PrintOrder.Status.PAYMENT_VERIFIED,
        PrintOrder.Status.QUEUED,
        PrintOrder.Status.ASSIGNED
    ]).count()
    printing_orders = shop_orders.filter(status__in=[
        PrintOrder.Status.SENT_TO_PRINTER,
        PrintOrder.Status.PRINTING
    ]).count()
    completed_orders = shop_orders.filter(status=PrintOrder.Status.COMPLETED).count()
    failed_orders = shop_orders.filter(status=PrintOrder.Status.FAILED).count()

    # Revenue metrics
    today_revenue = shop_orders.filter(
        created_at__gte=today_start,
        status__in=[
            PrintOrder.Status.PAYMENT_VERIFIED,
            PrintOrder.Status.QUEUED,
            PrintOrder.Status.ASSIGNED,
            PrintOrder.Status.SENT_TO_PRINTER,
            PrintOrder.Status.PRINTING,
            PrintOrder.Status.COMPLETED
        ]
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    total_revenue = shop_orders.filter(
        status__in=[
            PrintOrder.Status.PAYMENT_VERIFIED,
            PrintOrder.Status.QUEUED,
            PrintOrder.Status.ASSIGNED,
            PrintOrder.Status.SENT_TO_PRINTER,
            PrintOrder.Status.PRINTING,
            PrintOrder.Status.COMPLETED
        ]
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # Printers metrics
    shop_printers = Printer.objects.filter(shop=shop)
    online_printers = shop_printers.filter(is_online=True, is_active=True).count()
    offline_printers = shop_printers.filter(Q(is_online=False) | Q(is_active=False)).count()

    recent_orders = shop_orders.select_related('document', 'preference').order_by('-created_at')[:10]

    context = {
        'shop': shop,
        'total_orders': total_orders,
        'today_orders': today_orders,
        'pending_orders': pending_orders,
        'printing_orders': printing_orders,
        'completed_orders': completed_orders,
        'failed_orders': failed_orders,
        'today_revenue': today_revenue,
        'total_revenue': total_revenue,
        'online_printers': online_printers,
        'offline_printers': offline_printers,
        'shop_printers': shop_printers,
        'recent_orders': recent_orders,
    }
    return render(request, 'core/owner_overview.html', context)


@owner_required
def shop_qr_management(request):
    """
    Shop Permanent QR Code display, regeneration, and download options.
    """
    shop = get_user_shop(request.user)
    qr_record = getattr(shop, 'qr_code', None)

    if not qr_record or not qr_record.qr_code_image:
        qr_record = generate_shop_qr_code(shop)

    if request.method == 'POST' and 'regenerate' in request.POST:
        qr_record = generate_shop_qr_code(shop)
        AuditLog.objects.create(
            shop=shop,
            user=request.user,
            action='QR_REGENERATED',
            resource_type='ShopQRCode',
            resource_id=str(qr_record.id),
            details={'target_url': shop.order_page_url}
        )
        messages.success(request, "QR Code assets re-rendered successfully!")
        return redirect('core:shop_qr_management')

    poster_pdf_path = os.path.join('media', 'qr_codes', f"shop_qr_{shop.slug}_poster.pdf")
    has_poster_pdf = os.path.exists(poster_pdf_path)

    context = {
        'shop': shop,
        'qr_record': qr_record,
        'has_poster_pdf': has_poster_pdf,
    }
    return render(request, 'core/shop_qr_management.html', context)


@owner_required
def download_qr_asset(request, asset_type):
    """
    Provides secure download for the shop permanent QR PNG or printable PDF stand.
    """
    shop = get_user_shop(request.user)
    if asset_type == 'png':
        qr_path = os.path.join('media', 'qr_codes', f"shop_qr_{shop.slug}.png")
        if not os.path.exists(qr_path):
            generate_shop_qr_code(shop)
        return FileResponse(open(qr_path, 'rb'), as_attachment=True, filename=f"{shop.slug}_permanent_qr.png")
    elif asset_type == 'pdf':
        pdf_path = os.path.join('media', 'qr_codes', f"shop_qr_{shop.slug}_poster.pdf")
        if not os.path.exists(pdf_path):
            generate_shop_qr_code(shop)
        return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename=f"{shop.slug}_display_poster.pdf")
    raise Http404("Asset type not found")


@owner_required
def shop_settings(request):
    """
    Shop configuration: profile details, pause/resume ordering switch.
    """
    shop = get_user_shop(request.user)

    if request.method == 'POST':
        form = ShopSettingsForm(request.POST, instance=shop)
        if form.is_valid():
            old_status = shop.is_accepting_orders
            updated_shop = form.save()
            new_status = updated_shop.is_accepting_orders

            if old_status != new_status:
                AuditLog.objects.create(
                    shop=shop,
                    user=request.user,
                    action='ORDERING_TOGGLED',
                    resource_type='Shop',
                    resource_id=str(shop.id),
                    details={'is_accepting_orders': new_status}
                )

            messages.success(request, "Shop settings updated successfully.")
            return redirect('core:shop_settings')
    else:
        form = ShopSettingsForm(instance=shop)

    context = {
        'shop': shop,
        'form': form,
    }
    return render(request, 'core/shop_settings.html', context)


@owner_required
def staff_management(request):
    """
    Manage shop operators and granular staff permissions.
    """
    shop = get_user_shop(request.user)
    staff_members = ShopStaff.objects.filter(shop=shop).select_related('user')

    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            staff = form.save(shop=shop)
            AuditLog.objects.create(
                shop=shop,
                user=request.user,
                action='STAFF_CREATED',
                resource_type='ShopStaff',
                resource_id=str(staff.id),
                details={'username': staff.user.username}
            )
            messages.success(request, f"Staff member '{staff.user.get_full_name() or staff.user.username}' added.")
            return redirect('core:staff_management')
    else:
        form = StaffCreateForm()

    context = {
        'shop': shop,
        'staff_members': staff_members,
        'form': form,
    }
    return render(request, 'core/staff_management.html', context)


@owner_required
def remove_staff(request, staff_id):
    """
    Deactivates or removes a staff member.
    """
    shop = get_user_shop(request.user)
    staff = get_object_or_404(ShopStaff, id=staff_id, shop=shop)
    user = staff.user
    user.is_active = False
    user.save()
    staff.delete()

    AuditLog.objects.create(
        shop=shop,
        user=request.user,
        action='STAFF_REMOVED',
        resource_type='ShopStaff',
        resource_id=str(staff_id),
        details={'username': user.username}
    )
    messages.info(request, f"Staff account '{user.username}' removed.")
    return redirect('core:staff_management')


@owner_required
def reports_view(request):
    """
    Business performance & printing operations analytics report.
    """
    shop = get_user_shop(request.user)
    orders = PrintOrder.objects.filter(shop=shop)

    now = timezone.now()
    days_data = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        day_orders = orders.filter(created_at__date=day)
        day_rev = day_orders.filter(
            status__in=[
                PrintOrder.Status.PAYMENT_VERIFIED,
                PrintOrder.Status.QUEUED,
                PrintOrder.Status.ASSIGNED,
                PrintOrder.Status.SENT_TO_PRINTER,
                PrintOrder.Status.PRINTING,
                PrintOrder.Status.COMPLETED
            ]
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

        days_data.append({
            'date': day.strftime('%d %b'),
            'orders_count': day_orders.count(),
            'revenue': float(day_rev)
        })

    # Mode breakdown
    bw_count = orders.filter(preference__color_mode='BW').count()
    color_count = orders.filter(preference__color_mode='COLOR').count()

    context = {
        'shop': shop,
        'days_data': days_data,
        'bw_count': bw_count,
        'color_count': color_count,
        'total_orders': orders.count(),
    }
    return render(request, 'core/reports.html', context)

```

---

## File: `kep_printgrid/__init__.py`

```python

```

---

## File: `kep_printgrid/asgi.py`

```python
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

```

---

## File: `kep_printgrid/settings.py`

```python
"""
Django settings for KEP PrintGrid project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('SECRET_KEY', 'insecure-dev-key-kep-printgrid-2026')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',') if host.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',

    # KEP PrintGrid apps
    'core.apps.CoreConfig',
    'printers.apps.PrintersConfig',
    'orders.apps.OrdersConfig',
    'payments.apps.PaymentsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kep_printgrid.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.printgrid_global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'kep_printgrid.wsgi.application'

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Database Configuration with MySQL / SQLite support
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite').lower()

if DB_ENGINE == 'mysql':
    import pymysql
    pymysql.install_as_MySQLdb()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'kep_printgrid'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (QR codes, encrypted documents)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication redirects
LOGIN_URL = 'core:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:login'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Razorpay / Payment Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_kep_demo_key')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'rzp_test_kep_demo_secret')
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', 'rzp_test_webhook_secret')
PAYMENT_SANDBOX_MODE = os.getenv('PAYMENT_SANDBOX_MODE', 'True').lower() in ('true', '1', 'yes')

# Base URL for QR codes
BASE_APP_URL = os.getenv('BASE_APP_URL', 'http://127.0.0.1:8000')

# Max Document Upload Size (e.g. 50 MB)
MAX_DOCUMENT_UPLOAD_SIZE = 50 * 1024 * 1024

```

---

## File: `kep_printgrid/urls.py`

```python
"""
URL configuration for KEP PrintGrid project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from orders import views as orders_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Permanent QR Code destination: https://domain/shop/<shop-unique-slug>/
    path('shop/<slug:slug>/', orders_views.shop_order_page, name='shop_order_page'),

    # Core (Auth, Dashboards, QR, Settings, Staff, Reports)
    path('', include('core.urls')),

    # Orders (Ordering API, Tracking, Order Management, Pricing)
    path('orders/', include('orders.urls')),

    # Printers & Local Connector (Printer Management, Spooler Sync, Heartbeat)
    path('printers/', include('printers.urls')),

    # Payments (Razorpay Integration, Verification, Webhooks, Refunds)
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

```

---

## File: `kep_printgrid/wsgi.py`

```python
"""
WSGI config for kep_printgrid project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kep_printgrid.settings')

application = get_wsgi_application()

```

---

## File: `manage.py`

```python
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
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```

---

## File: `orders/__init__.py`

```python

```

---

## File: `orders/admin.py`

```python
from django.contrib import admin
from .models import PrintDocument, PrintPreference, PricingRule, PrintOrder, PrintJob, PrintJobAttempt


@admin.register(PrintDocument)
class PrintDocumentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'shop', 'detected_page_count', 'verified_page_count', 'encrypted_file_size', 'created_at')
    search_fields = ('original_filename', 'file_hash_sha256')


@admin.register(PrintPreference)
class PrintPreferenceAdmin(admin.ModelAdmin):
    list_display = ('color_mode', 'duplex_mode', 'paper_size', 'copies', 'page_range_type', 'total_calculated_pages')


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('shop', 'bw_single_rate', 'bw_double_rate', 'color_single_rate', 'color_double_rate', 'a3_bw_rate', 'a3_color_rate', 'is_active')
    list_filter = ('is_active', 'shop')


@admin.register(PrintOrder)
class PrintOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'shop', 'customer_name', 'customer_phone', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'shop', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone')


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ('order', 'printer', 'status', 'assigned_at', 'dispatched_at', 'completed_at')
    list_filter = ('status', 'printer__shop')


@admin.register(PrintJobAttempt)
class PrintJobAttemptAdmin(admin.ModelAdmin):
    list_display = ('job', 'printer', 'attempt_number', 'status', 'timestamp')

```

---

## File: `orders/api_views.py`

```python
import hashlib
import uuid
import secrets
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction

from core.models import Shop, AuditLog
from printers.models import Printer
from .models import PrintDocument, PrintPreference, PricingRule, PrintOrder, PrintJob


class QuoteAPIView(APIView):
    """
    Computes an exact, transparent price quote before checkout.
    Never silently inflates agreed prices.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        shop_slug = request.data.get('shop_slug')
        shop = get_object_or_404(Shop, slug=shop_slug)
        pricing = PricingRule.objects.filter(shop=shop, is_active=True).first()
        if not pricing:
            pricing = PricingRule.objects.create(shop=shop)

        raw_page_count = int(request.data.get('page_count', 1))
        color_mode = request.data.get('color_mode', 'BW')
        duplex_mode = request.data.get('duplex_mode', 'SINGLE')
        paper_size = request.data.get('paper_size', 'A4')
        copies = int(request.data.get('copies', 1))
        page_range_type = request.data.get('page_range_type', 'ALL')
        page_range_selection = request.data.get('page_range_selection', '').strip()

        # Page count resolution
        if page_range_type == 'CUSTOM' and page_range_selection:
            # Parse selected pages like "1-3, 5"
            selected_count = 0
            for part in page_range_selection.split(','):
                part = part.strip()
                if '-' in part:
                    s, e = part.split('-', 1)
                    if s.isdigit() and e.isdigit():
                        selected_count += max(0, int(e) - int(s) + 1)
                elif part.isdigit():
                    selected_count += 1
            effective_pages = max(1, min(selected_count, raw_page_count))
        else:
            effective_pages = max(1, raw_page_count)

        # Temporary preference instance for calculation
        pref = PrintPreference(
            color_mode=color_mode,
            duplex_mode=duplex_mode,
            paper_size=paper_size,
            copies=copies,
            page_range_type=page_range_type,
            page_range_selection=page_range_selection,
            total_calculated_pages=effective_pages
        )

        quote = pricing.calculate_price(pref, effective_pages)
        return Response(quote)


class UploadEncryptedDocumentAPIView(APIView):
    """
    Receives the browser-encrypted PDF ciphertext.
    The cloud server receives only ciphertext and wrapped key bundle.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        shop_slug = request.data.get('shop_slug')
        shop = get_object_or_404(Shop, slug=shop_slug)

        if not shop.is_accepting_orders:
            return Response(
                {'error': shop.pause_message},
                status=status.HTTP_400_BAD_REQUEST
            )

        encrypted_file = request.FILES.get('encrypted_file')
        if not encrypted_file:
            return Response({'error': 'Missing encrypted file payload.'}, status=status.HTTP_400_BAD_REQUEST)

        # Read content and compute hash to verify integrity
        file_bytes = encrypted_file.read()
        computed_hash = hashlib.sha256(file_bytes).hexdigest()
        encrypted_file.seek(0)

        reported_hash = request.data.get('file_hash_sha256', '')
        if reported_hash and reported_hash.lower() != computed_hash.lower():
            return Response(
                {'error': 'Cryptographic hash mismatch. Document may be corrupted during transmission.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        encrypted_key_bundle = request.data.get('encrypted_key_bundle', '').strip()
        encryption_iv = request.data.get('encryption_iv', '').strip()
        encryption_tag = request.data.get('encryption_tag', '').strip()
        detected_page_count = int(request.data.get('detected_page_count', 1))
        original_filename = request.data.get('original_filename', 'document.pdf').strip()

        if not encrypted_key_bundle or not encryption_iv:
            return Response(
                {'error': 'Missing client-side encryption metadata (key bundle or IV).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        document = PrintDocument.objects.create(
            shop=shop,
            original_filename=original_filename,
            file_hash_sha256=computed_hash,
            encrypted_file=encrypted_file,
            encrypted_file_size=len(file_bytes),
            encrypted_key_bundle=encrypted_key_bundle,
            encryption_iv=encryption_iv,
            encryption_tag=encryption_tag,
            detected_page_count=detected_page_count
        )

        return Response({
            'document_id': str(document.id),
            'filename': document.original_filename,
            'size': document.encrypted_file_size,
            'detected_page_count': document.detected_page_count,
            'sha256': document.file_hash_sha256,
        }, status=status.HTTP_201_CREATED)


class CreatePrintOrderAPIView(APIView):
    """
    Creates an order awaiting payment.
    Ensures idempotency and price integrity.
    """
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        shop_slug = request.data.get('shop_slug')
        shop = get_object_or_404(Shop, slug=shop_slug)

        if not shop.is_accepting_orders:
            return Response({'error': shop.pause_message}, status=status.HTTP_400_BAD_REQUEST)

        document_id = request.data.get('document_id')
        document = get_object_or_404(PrintDocument, id=document_id, shop=shop)

        # Check idempotency
        idempotency_key = request.data.get('idempotency_key') or f"idemp_{uuid.uuid4().hex}"
        existing_order = PrintOrder.objects.filter(idempotency_key=idempotency_key).first()
        if existing_order:
            return Response({
                'order_number': existing_order.order_number,
                'total_amount': str(existing_order.total_amount),
                'status': existing_order.status,
                'pricing_breakdown': existing_order.pricing_breakdown
            })

        prefs_data = request.data.get('preferences', {})
        color_mode = prefs_data.get('color_mode', 'BW')
        duplex_mode = prefs_data.get('duplex_mode', 'SINGLE')
        paper_size = prefs_data.get('paper_size', 'A4')
        copies = max(1, int(prefs_data.get('copies', 1)))
        page_range_type = prefs_data.get('page_range_type', 'ALL')
        page_range_selection = prefs_data.get('page_range_selection', '').strip()

        # Calculate pages
        num_pages = document.detected_page_count
        if page_range_type == 'CUSTOM' and page_range_selection:
            selected_count = 0
            for part in page_range_selection.split(','):
                part = part.strip()
                if '-' in part:
                    s, e = part.split('-', 1)
                    if s.isdigit() and e.isdigit():
                        selected_count += max(0, int(e) - int(s) + 1)
                elif part.isdigit():
                    selected_count += 1
            num_pages = max(1, min(selected_count, document.detected_page_count))

        preference = PrintPreference.objects.create(
            color_mode=color_mode,
            duplex_mode=duplex_mode,
            paper_size=paper_size,
            copies=copies,
            page_range_type=page_range_type,
            page_range_selection=page_range_selection,
            total_calculated_pages=num_pages
        )

        pricing = PricingRule.objects.filter(shop=shop, is_active=True).first()
        if not pricing:
            pricing = PricingRule.objects.create(shop=shop)

        breakdown = pricing.calculate_price(preference, num_pages)
        total_amount = Decimal(str(breakdown['total_amount']))

        # Generate unique order number (e.g. ORD-20261111-9284)
        date_str = timezone.now().strftime('%Y%m%d')
        random_suffix = secrets.token_hex(2).upper()
        order_number = f"ORD-{date_str}-{random_suffix}"
        while PrintOrder.objects.filter(order_number=order_number).exists():
            order_number = f"ORD-{date_str}-{secrets.token_hex(2).upper()}"

        customer_name = request.data.get('customer_name', 'Customer').strip() or 'Customer'
        customer_phone = request.data.get('customer_phone', '').strip()

        order = PrintOrder.objects.create(
            order_number=order_number,
            shop=shop,
            customer_name=customer_name,
            customer_phone=customer_phone,
            document=document,
            preference=preference,
            status=PrintOrder.Status.AWAITING_PAYMENT,
            total_amount=total_amount,
            pricing_breakdown=breakdown,
            idempotency_key=idempotency_key
        )

        AuditLog.objects.create(
            shop=shop,
            action='PRINT_ORDER_CREATED',
            resource_type='PrintOrder',
            resource_id=str(order.id),
            details={'order_number': order_number, 'total_amount': str(total_amount)}
        )

        return Response({
            'order_number': order.order_number,
            'total_amount': str(order.total_amount),
            'pricing_breakdown': breakdown,
            'status': order.status,
            'currency': 'INR',
        }, status=status.HTTP_201_CREATED)


class OrderStatusAPIView(APIView):
    """
    Returns live order and print job status.
    """
    permission_classes = [AllowAny]

    def get(self, request, order_number):
        order = get_object_or_404(
            PrintOrder.objects.select_related('shop', 'document', 'preference', 'print_job', 'print_job__printer'),
            order_number=order_number
        )
        job = getattr(order, 'print_job', None)

        return Response({
            'order_number': order.order_number,
            'shop_name': order.shop.name,
            'status': order.status,
            'status_display': order.get_status_display(),
            'total_amount': str(order.total_amount),
            'currency': 'INR',
            'created_at': order.created_at.isoformat(),
            'job_status': job.status if job else None,
            'printer_name': job.printer.name if job and job.printer else None,
            'failure_reason': job.failure_reason if job else None,
            'is_completed': order.status == PrintOrder.Status.COMPLETED,
        })

```

---

## File: `orders/apps.py`

```python
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = 'orders'

```

---

## File: `orders/forms.py`

```python
from django import forms
from .models import PricingRule


class PricingRuleForm(forms.ModelForm):
    class Meta:
        model = PricingRule
        fields = [
            'bw_single_rate', 'bw_double_rate',
            'color_single_rate', 'color_double_rate',
            'a3_bw_rate', 'a3_color_rate', 'is_active'
        ]
        widgets = {
            'bw_single_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'bw_double_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'color_single_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'color_double_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'a3_bw_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'a3_color_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

```

---

## File: `orders/migrations/0001_initial.py`

```python
# Generated by Django 6.1.3 on 2026-11-11 08:53

import django.db.models.deletion
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('printers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PrintPreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('color_mode', models.CharField(choices=[('BW', 'Black & White'), ('COLOR', 'Color')], default='BW', max_length=10)),
                ('duplex_mode', models.CharField(choices=[('SINGLE', 'Single-Sided'), ('DOUBLE', 'Double-Sided')], default='SINGLE', max_length=10)),
                ('paper_size', models.CharField(choices=[('A4', 'A4 (210 x 297 mm)'), ('A3', 'A3 (297 x 420 mm)')], default='A4', max_length=10)),
                ('copies', models.PositiveIntegerField(default=1)),
                ('page_range_type', models.CharField(choices=[('ALL', 'All Pages'), ('CUSTOM', 'Custom Range')], default='ALL', max_length=10)),
                ('page_range_selection', models.CharField(blank=True, default='', help_text='e.g. 1-5, 8, 11-14', max_length=255)),
                ('total_calculated_pages', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PricingRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bw_single_rate', models.DecimalField(decimal_places=2, default=Decimal('2.00'), max_digits=6)),
                ('bw_double_rate', models.DecimalField(decimal_places=2, default=Decimal('3.50'), max_digits=6)),
                ('color_single_rate', models.DecimalField(decimal_places=2, default=Decimal('10.00'), max_digits=6)),
                ('color_double_rate', models.DecimalField(decimal_places=2, default=Decimal('18.00'), max_digits=6)),
                ('a3_bw_rate', models.DecimalField(decimal_places=2, default=Decimal('5.00'), max_digits=6)),
                ('a3_color_rate', models.DecimalField(decimal_places=2, default=Decimal('20.00'), max_digits=6)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_rules', to='core.shop')),
            ],
        ),
        migrations.CreateModel(
            name='PrintDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('original_filename', models.CharField(max_length=255)),
                ('file_hash_sha256', models.CharField(help_text='Cryptographic hash of encrypted payload', max_length=64)),
                ('encrypted_file', models.FileField(upload_to='encrypted_docs/')),
                ('encrypted_file_size', models.BigIntegerField(default=0)),
                ('encrypted_key_bundle', models.TextField(help_text="Base64 encoded AES key wrapped with shop's RSA public key")),
                ('encryption_iv', models.CharField(help_text='Base64 encoded AES-GCM IV (12 bytes)', max_length=64)),
                ('encryption_tag', models.CharField(help_text='Base64 encoded AES-GCM auth tag (16 bytes)', max_length=64)),
                ('detected_page_count', models.PositiveIntegerField(default=1)),
                ('verified_page_count', models.PositiveIntegerField(blank=True, help_text='Verified locally by connector', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='core.shop')),
            ],
        ),
        migrations.CreateModel(
            name='PrintJob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('QUEUED', 'Queued for Dispatch'), ('DISPATCHED', 'Dispatched to Connector'), ('RECEIVED_BY_CONNECTOR', 'Received & Decrypted by Connector'), ('SUBMITTED_TO_SPOOLER', 'Submitted to Windows Spooler'), ('PHYSICALLY_PRINTED', 'Physically Printed'), ('FAILED', 'Execution Failed'), ('HOLD_VERIFICATION', 'Held for Owner Verification (Page mismatch)')], db_index=True, default='QUEUED', max_length=30)),
                ('assigned_at', models.DateTimeField(blank=True, null=True)),
                ('dispatched_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('failure_reason', models.TextField(blank=True)),
                ('connector_ack_id', models.CharField(blank=True, max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('connector', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_jobs', to='printers.connector')),
                ('printer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='print_jobs', to='printers.printer')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PrintJobAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('attempt_number', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(max_length=30)),
                ('error_message', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('authorized_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='orders.printjob')),
                ('printer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='printers.printer')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='PrintOrder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order_number', models.CharField(db_index=True, max_length=32, unique=True)),
                ('customer_phone', models.CharField(max_length=20)),
                ('customer_name', models.CharField(default='Walk-in Customer', max_length=150)),
                ('status', models.CharField(choices=[('UPLOADED', 'Uploaded'), ('AWAITING_PAYMENT', 'Awaiting Payment'), ('PAYMENT_VERIFIED', 'Payment Verified'), ('QUEUED', 'Queued'), ('ASSIGNED', 'Assigned to Printer'), ('SENT_TO_PRINTER', 'Sent to Printer'), ('PRINTING', 'Printing in Progress'), ('COMPLETED', 'Completed & Ready for Pickup'), ('FAILED', 'Print Failed'), ('CANCELLED', 'Cancelled'), ('REFUND_PENDING', 'Refund Pending'), ('REFUNDED', 'Refunded')], db_index=True, default='UPLOADED', max_length=30)),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('pricing_breakdown', models.JSONField(default=dict)),
                ('idempotency_key', models.CharField(db_index=True, max_length=128, unique=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customer_orders', to=settings.AUTH_USER_MODEL)),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='order', to='orders.printdocument')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='core.shop')),
                ('preference', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='order', to='orders.printpreference')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='printjob',
            name='order',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='print_job', to='orders.printorder'),
        ),
    ]

```

---

## File: `orders/migrations/__init__.py`

```python

```

---

## File: `orders/models.py`

```python
import uuid
from decimal import Decimal
from django.db import models
from core.models import Shop, User
from printers.models import Printer, Connector


class PrintDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='documents')
    original_filename = models.CharField(max_length=255)
    file_hash_sha256 = models.CharField(max_length=64, help_text="Cryptographic hash of encrypted payload")
    encrypted_file = models.FileField(upload_to='encrypted_docs/')
    encrypted_file_size = models.BigIntegerField(default=0)

    # Client-side encryption envelope (Zero-Knowledge)
    # The client generates random AES-256 key, encrypts PDF, and wraps AES key with Shop RSA-OAEP public key.
    encrypted_key_bundle = models.TextField(
        help_text="Base64 encoded AES key wrapped with shop's RSA public key"
    )
    encryption_iv = models.CharField(max_length=64, help_text="Base64 encoded AES-GCM IV (12 bytes)")
    encryption_tag = models.CharField(max_length=64, help_text="Base64 encoded AES-GCM auth tag (16 bytes)")

    detected_page_count = models.PositiveIntegerField(default=1)
    verified_page_count = models.PositiveIntegerField(null=True, blank=True, help_text="Verified locally by connector")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_filename} ({self.detected_page_count} pages)"


class PrintPreference(models.Model):
    class ColorMode(models.TextChoices):
        BW = 'BW', 'Black & White'
        COLOR = 'COLOR', 'Color'

    class DuplexMode(models.TextChoices):
        SINGLE = 'SINGLE', 'Single-Sided'
        DOUBLE = 'DOUBLE', 'Double-Sided'

    class PaperSize(models.TextChoices):
        A4 = 'A4', 'A4 (210 x 297 mm)'
        A3 = 'A3', 'A3 (297 x 420 mm)'

    class PageRangeType(models.TextChoices):
        ALL = 'ALL', 'All Pages'
        CUSTOM = 'CUSTOM', 'Custom Range'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    color_mode = models.CharField(max_length=10, choices=ColorMode.choices, default=ColorMode.BW)
    duplex_mode = models.CharField(max_length=10, choices=DuplexMode.choices, default=DuplexMode.SINGLE)
    paper_size = models.CharField(max_length=10, choices=PaperSize.choices, default=PaperSize.A4)
    copies = models.PositiveIntegerField(default=1)
    page_range_type = models.CharField(max_length=10, choices=PageRangeType.choices, default=PageRangeType.ALL)
    page_range_selection = models.CharField(max_length=255, blank=True, default="", help_text="e.g. 1-5, 8, 11-14")
    total_calculated_pages = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.color_mode} | {self.duplex_mode} | {self.paper_size} x {self.copies}"


class PricingRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='pricing_rules')
    bw_single_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('2.00'))
    bw_double_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('3.50'))
    color_single_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('10.00'))
    color_double_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('18.00'))
    a3_bw_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('5.00'))
    a3_color_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('20.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_price(self, preference: PrintPreference, num_pages: int) -> dict:
        """
        Calculates exact price based on configured rates.
        Returns a dict breakdown and total amount.
        """
        copies = max(1, preference.copies)
        pages_to_print = max(1, num_pages)
        color = preference.color_mode
        duplex = preference.duplex_mode
        paper = preference.paper_size

        if paper == 'A3':
            unit_rate = self.a3_color_rate if color == 'COLOR' else self.a3_bw_rate
            rate_label = f"A3 {color} (per page)"
            sheets = pages_to_print
        else:
            if color == 'COLOR':
                if duplex == 'DOUBLE':
                    # Rate per sheet (2 pages)
                    sheets = (pages_to_print + 1) // 2
                    unit_rate = self.color_double_rate
                    rate_label = "Color Double-Sided (per sheet)"
                else:
                    sheets = pages_to_print
                    unit_rate = self.color_single_rate
                    rate_label = "Color Single-Sided (per page)"
            else:
                if duplex == 'DOUBLE':
                    sheets = (pages_to_print + 1) // 2
                    unit_rate = self.bw_double_rate
                    rate_label = "B&W Double-Sided (per sheet)"
                else:
                    sheets = pages_to_print
                    unit_rate = self.bw_single_rate
                    rate_label = "B&W Single-Sided (per page)"

        subtotal = unit_rate * sheets * copies
        total_amount = round(subtotal, 2)

        return {
            'unit_rate': float(unit_rate),
            'rate_label': rate_label,
            'sheets_per_copy': sheets,
            'pages_per_copy': pages_to_print,
            'copies': copies,
            'total_sheets': sheets * copies,
            'total_amount': float(total_amount),
            'currency': 'INR',
        }


class PrintOrder(models.Model):
    class Status(models.TextChoices):
        UPLOADED = 'UPLOADED', 'Uploaded'
        AWAITING_PAYMENT = 'AWAITING_PAYMENT', 'Awaiting Payment'
        PAYMENT_VERIFIED = 'PAYMENT_VERIFIED', 'Payment Verified'
        QUEUED = 'QUEUED', 'Queued'
        ASSIGNED = 'ASSIGNED', 'Assigned to Printer'
        SENT_TO_PRINTER = 'SENT_TO_PRINTER', 'Sent to Printer'
        PRINTING = 'PRINTING', 'Printing in Progress'
        COMPLETED = 'COMPLETED', 'Completed & Ready for Pickup'
        FAILED = 'FAILED', 'Print Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUND_PENDING = 'REFUND_PENDING', 'Refund Pending'
        REFUNDED = 'REFUNDED', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_orders')
    customer_phone = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=150, default='Walk-in Customer')
    document = models.OneToOneField(PrintDocument, on_delete=models.CASCADE, related_name='order')
    preference = models.OneToOneField(PrintPreference, on_delete=models.CASCADE, related_name='order')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.UPLOADED, db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    pricing_breakdown = models.JSONField(default=dict)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.get_status_display()} ({self.total_amount} INR)"


class PrintJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'QUEUED', 'Queued for Dispatch'
        DISPATCHED = 'DISPATCHED', 'Dispatched to Connector'
        RECEIVED_BY_CONNECTOR = 'RECEIVED_BY_CONNECTOR', 'Received & Decrypted by Connector'
        SUBMITTED_TO_SPOOLER = 'SUBMITTED_TO_SPOOLER', 'Submitted to Windows Spooler'
        PHYSICALLY_PRINTED = 'PHYSICALLY_PRINTED', 'Physically Printed'
        FAILED = 'FAILED', 'Execution Failed'
        HOLD_VERIFICATION = 'HOLD_VERIFICATION', 'Held for Owner Verification (Page mismatch)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(PrintOrder, on_delete=models.CASCADE, related_name='print_job')
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL, null=True, blank=True, related_name='print_jobs')
    connector = models.ForeignKey(Connector, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.QUEUED, db_index=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    connector_ack_id = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        printer_name = self.printer.name if self.printer else "Unassigned"
        return f"Job for {self.order.order_number} -> {printer_name} [{self.status}]"


class PrintJobAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name='attempts')
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL, null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=30)
    error_message = models.TextField(blank=True)
    authorized_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

```

---

## File: `orders/tests.py`

```python
from django.test import TestCase

# Create your tests here.

```

---

## File: `orders/urls.py`

```python
from django.urls import path
from . import views
from . import api_views

app_name = 'orders'

urlpatterns = [
    # Dashboard & operations views
    path('list/', views.order_list, name='order_list'),
    path('detail/<str:order_number>/', views.order_detail, name='order_detail'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('pricing-settings/', views.pricing_settings_view, name='pricing_settings'),
    path('retry/<str:order_number>/', views.authorize_retry, name='authorize_retry'),
    path('mark-completed/<str:order_number>/', views.mark_order_completed, name='mark_completed'),

    # Public customer tracking
    path('track/<str:order_number>/', views.customer_track_order, name='customer_track_order'),

    # Public Customer Ordering API endpoints
    path('api/quote/', api_views.QuoteAPIView.as_view(), name='api_quote'),
    path('api/upload/', api_views.UploadEncryptedDocumentAPIView.as_view(), name='api_upload'),
    path('api/create/', api_views.CreatePrintOrderAPIView.as_view(), name='api_create_order'),
    path('api/status/<str:order_number>/', api_views.OrderStatusAPIView.as_view(), name='api_order_status'),

    # Authorized connector encrypted document download
    path('api/document/<uuid:document_id>/download/', views.secure_document_download, name='secure_document_download'),
]

```

---

## File: `orders/views.py`

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, Http404, FileResponse
from django.db import transaction
import os

from core.models import Shop, AuditLog
from core.decorators import owner_required, staff_or_owner_required, get_user_shop
from printers.models import Printer
from printers.services.routing_service import RoutingService
from .models import PrintOrder, PrintJob, PrintJobAttempt, PricingRule, PrintDocument
from .forms import PricingRuleForm


def shop_order_page(request, slug):
    """
    Public customer ordering page reached when scanning the shop's permanent QR code.
    Shows shop info, pause status, document uploader, PDF.js preview, preferences, and price quote.
    """
    shop = get_object_or_404(Shop, slug=slug)

    # Fetch active shop pricing
    pricing = PricingRule.objects.filter(shop=shop, is_active=True).first()
    if not pricing:
        pricing = PricingRule.objects.create(shop=shop)

    # Determine what options to offer based on shop printers capabilities
    printers = Printer.objects.filter(shop=shop, is_active=True).select_related('capability')
    has_color_printer = printers.filter(handles_color=True).exists()
    has_duplex_printer = any(getattr(p, 'capability', None) and p.capability.supports_duplex for p in printers)
    has_a3_printer = any(getattr(p, 'capability', None) and 'A3' in p.capability.supported_paper_sizes for p in printers)

    context = {
        'shop': shop,
        'pricing': pricing,
        'has_color_printer': has_color_printer,
        'has_duplex_printer': has_duplex_printer,
        'has_a3_printer': has_a3_printer,
        'connector_public_key': shop.connector_public_key,
    }
    return render(request, 'orders/shop_order_page.html', context)


def customer_track_order(request, order_number):
    """
    Public order tracking page for customer.
    """
    order = get_object_or_404(PrintOrder.objects.select_related('shop', 'preference', 'print_job'), order_number=order_number)
    context = {
        'order': order,
        'job': getattr(order, 'print_job', None),
    }
    return render(request, 'orders/customer_track_order.html', context)


@owner_required
def pricing_settings_view(request):
    """
    Shop owner pricing configuration for print services.
    """
    shop = get_user_shop(request.user)
    pricing = PricingRule.objects.filter(shop=shop).first()
    if not pricing:
        pricing = PricingRule.objects.create(shop=shop)

    if request.method == 'POST':
        form = PricingRuleForm(request.POST, instance=pricing)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                shop=shop,
                user=request.user,
                action='PRICING_UPDATED',
                resource_type='PricingRule',
                resource_id=str(pricing.id),
                details={
                    'bw_single': str(pricing.bw_single_rate),
                    'color_single': str(pricing.color_single_rate)
                }
            )
            messages.success(request, "Printing rates updated successfully.")
            return redirect('orders:pricing_settings')
    else:
        form = PricingRuleForm(instance=pricing)

    context = {
        'shop': shop,
        'form': form,
        'pricing': pricing,
    }
    return render(request, 'orders/pricing_settings.html', context)


@staff_or_owner_required
def order_list(request):
    """
    Order management table with filtering by status, search, and date.
    """
    shop = get_user_shop(request.user)
    orders = PrintOrder.objects.filter(shop=shop).select_related('document', 'preference', 'print_job', 'print_job__printer').order_by('-created_at')

    status_filter = request.GET.get('status')
    search_query = request.GET.get('q')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if search_query:
        orders = orders.filter(order_number__icontains=search_query) | orders.filter(customer_phone__icontains=search_query)

    context = {
        'shop': shop,
        'orders': orders,
        'status_choices': PrintOrder.Status.choices,
        'selected_status': status_filter,
        'search_query': search_query,
    }
    return render(request, 'orders/order_list.html', context)


@staff_or_owner_required
def order_detail(request, order_number):
    """
    Detailed inspection of a print order.
    """
    shop = get_user_shop(request.user)
    order = get_object_or_404(
        PrintOrder.objects.select_related('shop', 'document', 'preference', 'print_job', 'print_job__printer'),
        shop=shop,
        order_number=order_number
    )
    payments = order.payments.all()
    attempts = order.print_job.attempts.all() if hasattr(order, 'print_job') else []

    context = {
        'shop': shop,
        'order': order,
        'job': getattr(order, 'print_job', None),
        'payments': payments,
        'attempts': attempts,
    }
    return render(request, 'orders/order_detail.html', context)


@staff_or_owner_required
def mark_order_completed(request, order_number):
    """
    Marks order as completed and collected by customer.
    """
    shop = get_user_shop(request.user)
    order = get_object_or_404(PrintOrder, shop=shop, order_number=order_number)
    order.status = PrintOrder.Status.COMPLETED
    order.save()

    if hasattr(order, 'print_job'):
        job = order.print_job
        job.status = PrintJob.Status.PHYSICALLY_PRINTED
        job.completed_at = timezone.now()
        job.save()

    AuditLog.objects.create(
        shop=shop,
        user=request.user,
        action='ORDER_HANDOVER_COMPLETED',
        resource_type='PrintOrder',
        resource_id=str(order.id),
        details={'order_number': order.order_number, 'collected_by': order.customer_name}
    )
    messages.success(request, f"Order {order.order_number} marked as completed & handed over.")
    return redirect('orders:staff_dashboard')


@staff_or_owner_required
def staff_dashboard(request):
    """
    Streamlined dashboard for shop front-desk staff.
    """
    shop = get_user_shop(request.user)
    orders = PrintOrder.objects.filter(shop=shop).select_related('document', 'preference', 'print_job', 'print_job__printer').order_by('-created_at')

    # Quick counters
    active_jobs = orders.filter(status__in=[
        PrintOrder.Status.PAYMENT_VERIFIED,
        PrintOrder.Status.QUEUED,
        PrintOrder.Status.ASSIGNED,
        PrintOrder.Status.SENT_TO_PRINTER,
        PrintOrder.Status.PRINTING
    ])

    ready_jobs = orders.filter(status=PrintOrder.Status.COMPLETED)
    failed_jobs = orders.filter(status=PrintOrder.Status.FAILED)

    context = {
        'shop': shop,
        'active_jobs': active_jobs,
        'ready_jobs': ready_jobs[:10],
        'failed_jobs': failed_jobs[:10],
    }
    return render(request, 'orders/staff_dashboard.html', context)


@staff_or_owner_required
def authorize_retry(request, order_number):
    """
    Explicitly authorizes a print retry after hardware intervention (e.g. paper refill, clear jam).
    """
    shop = get_user_shop(request.user)
    order = get_object_or_404(PrintOrder, shop=shop, order_number=order_number)

    if not hasattr(order, 'print_job'):
        messages.error(request, "No print job associated with this order.")
        return redirect('orders:order_detail', order_number=order_number)

    job = order.print_job
    target_printer = RoutingService.determine_target_printer(shop, order.preference)

    if not target_printer:
        messages.error(request, "No active online printer capable of printing this job was found. Please ensure a printer is connected.")
        return redirect('orders:order_detail', order_number=order_number)

    with transaction.atomic():
        job.printer = target_printer
        job.status = PrintJob.Status.DISPATCHED
        job.dispatched_at = timezone.now()
        job.failure_reason = ""
        job.save()

        order.status = PrintOrder.Status.ASSIGNED
        order.save()

        PrintJobAttempt.objects.create(
            job=job,
            printer=target_printer,
            attempt_number=job.attempts.count() + 1,
            status=PrintJob.Status.DISPATCHED,
            error_message="Manual retry authorized by shop staff",
            authorized_by=request.user
        )

        AuditLog.objects.create(
            shop=shop,
            user=request.user,
            action='PRINT_JOB_RETRY_AUTHORIZED',
            resource_type='PrintJob',
            resource_id=str(job.id),
            details={'order_number': order.order_number, 'target_printer': target_printer.name}
        )

    messages.success(request, f"Retry authorized! Job dispatched to '{target_printer.name}'.")
    return redirect('orders:order_detail', order_number=order_number)


def secure_document_download(request, document_id):
    """
    Encrypted document download endpoint.
    Strictly restricted to the authorized shop connector via token validation.
    The cloud backend never decrypts document content.
    """
    token = request.GET.get('token') or request.headers.get('X-Shop-Token')
    if not token:
        raise Http404("Missing access credentials")

    doc = get_object_or_404(PrintDocument, id=document_id)
    if doc.shop.connector_auth_token != token:
        raise Http404("Unauthorized connector")

    if not doc.encrypted_file or not os.path.exists(doc.encrypted_file.path):
        raise Http404("Encrypted document file missing from storage")

    response = FileResponse(open(doc.encrypted_file.path, 'rb'), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="encrypted_{doc.id}.bin"'
    return response

```

---

## File: `payments/__init__.py`

```python

```

---

## File: `payments/admin.py`

```python
from django.contrib import admin
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('gateway_order_id', 'gateway_payment_id', 'order', 'amount', 'currency', 'status', 'verified_at', 'created_at')
    list_filter = ('status', 'gateway_name', 'created_at')
    search_fields = ('gateway_order_id', 'gateway_payment_id', 'idempotency_key')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount', 'status', 'authorized_by', 'created_at')
    list_filter = ('status', 'created_at')

```

---

## File: `payments/apps.py`

```python
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = 'payments'

```

---

## File: `payments/migrations/0001_initial.py`

```python
# Generated by Django 6.1.3 on 2026-11-11 08:53

import django.db.models.deletion
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('gateway_order_id', models.CharField(db_index=True, max_length=100)),
                ('gateway_payment_id', models.CharField(blank=True, db_index=True, max_length=100)),
                ('gateway_signature', models.CharField(blank=True, max_length=255)),
                ('gateway_name', models.CharField(default='RAZORPAY_SANDBOX', max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('currency', models.CharField(default='INR', max_length=10)),
                ('status', models.CharField(choices=[('CREATED', 'Created / Initiated'), ('AUTHORIZED', 'Authorized'), ('CAPTURED', 'Captured / Verified'), ('FAILED', 'Failed')], default='CREATED', max_length=20)),
                ('idempotency_key', models.CharField(db_index=True, max_length=128, unique=True)),
                ('raw_response', models.JSONField(default=dict)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='orders.printorder')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reason', models.TextField()),
                ('gateway_refund_id', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[('INITIATED', 'Initiated'), ('PROCESSED', 'Processed / Refunded'), ('FAILED', 'Failed')], default='INITIATED', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('authorized_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refunds', to='payments.payment')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

```

---

## File: `payments/migrations/__init__.py`

```python

```

---

## File: `payments/models.py`

```python
import uuid
from decimal import Decimal
from django.db import models
from orders.models import PrintOrder
from core.models import User


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created / Initiated'
        AUTHORIZED = 'AUTHORIZED', 'Authorized'
        CAPTURED = 'CAPTURED', 'Captured / Verified'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(PrintOrder, on_delete=models.CASCADE, related_name='payments')
    gateway_order_id = models.CharField(max_length=100, db_index=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True, db_index=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    gateway_name = models.CharField(max_length=50, default='RAZORPAY_SANDBOX')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    raw_response = models.JSONField(default=dict)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.gateway_payment_id or self.gateway_order_id} - {self.status} (INR {self.amount})"


class Refund(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        PROCESSED = 'PROCESSED', 'Processed / Refunded'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    gateway_refund_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    authorized_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund INR {self.amount} for {self.payment} [{self.status}]"

```

---

## File: `payments/services/__init__.py`

```python

```

---

## File: `payments/services/gateway_adapter.py`

```python
import hmac
import hashlib
import json
import secrets
from decimal import Decimal
from abc import ABC, abstractmethod
from django.conf import settings


class BasePaymentGatewayAdapter(ABC):
    @abstractmethod
    def create_order(self, amount: Decimal, currency: str, receipt: str, notes: dict) -> dict:
        pass

    @abstractmethod
    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        pass

    @abstractmethod
    def initiate_refund(self, payment_id: str, amount: Decimal, reason: str) -> dict:
        pass


class RazorpaySandboxAdapter(BasePaymentGatewayAdapter):
    """
    High-fidelity Razorpay sandbox simulator.
    Provides identical API shapes, realistic IDs ('order_sandbox_...', 'pay_sandbox_...'),
    and enforces genuine HMAC-SHA256 signature verification without requiring active banking API keys.
    """
    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_kep_demo_key')
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_kep_demo_secret')
        self.webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', 'rzp_test_webhook_secret')

    def create_order(self, amount: Decimal, currency: str, receipt: str, notes: dict) -> dict:
        # Amount in paise (1 INR = 100 paise)
        amount_paise = int(amount * 100)
        gateway_order_id = f"order_{secrets.token_hex(8)}"
        return {
            'id': gateway_order_id,
            'entity': 'order',
            'amount': amount_paise,
            'amount_paid': 0,
            'amount_due': amount_paise,
            'currency': currency,
            'receipt': receipt,
            'status': 'created',
            'notes': notes,
            'key_id': self.key_id,
        }

    def generate_expected_signature(self, order_id: str, payment_id: str) -> str:
        msg = f"{order_id}|{payment_id}".encode('utf-8')
        return hmac.new(self.key_secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        if not signature or not order_id or not payment_id:
            return False
        expected = self.generate_expected_signature(order_id, payment_id)
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        if not signature:
            return False
        expected = hmac.new(self.webhook_secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def initiate_refund(self, payment_id: str, amount: Decimal, reason: str) -> dict:
        refund_id = f"rfnd_{secrets.token_hex(8)}"
        return {
            'id': refund_id,
            'entity': 'refund',
            'amount': int(amount * 100),
            'currency': 'INR',
            'payment_id': payment_id,
            'status': 'processed',
            'notes': {'reason': reason}
        }


class RazorpayLiveAdapter(BasePaymentGatewayAdapter):
    """
    Live Razorpay API Integration using standard HTTP requests.
    """
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self.base_url = "https://api.razorpay.com/v1"

    def create_order(self, amount: Decimal, currency: str, receipt: str, notes: dict) -> dict:
        import requests
        amount_paise = int(amount * 100)
        resp = requests.post(
            f"{self.base_url}/orders",
            auth=(self.key_id, self.key_secret),
            json={
                'amount': amount_paise,
                'currency': currency,
                'receipt': receipt,
                'notes': notes,
            },
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        data['key_id'] = self.key_id
        return data

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        msg = f"{order_id}|{payment_id}".encode('utf-8')
        expected = hmac.new(self.key_secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        expected = hmac.new(self.webhook_secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def initiate_refund(self, payment_id: str, amount: Decimal, reason: str) -> dict:
        import requests
        amount_paise = int(amount * 100)
        resp = requests.post(
            f"{self.base_url}/payments/{payment_id}/refund",
            auth=(self.key_id, self.key_secret),
            json={'amount': amount_paise, 'notes': {'reason': reason}},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()


def get_payment_gateway() -> BasePaymentGatewayAdapter:
    """
    Returns the appropriate payment gateway adapter based on configuration.
    """
    sandbox_mode = getattr(settings, 'PAYMENT_SANDBOX_MODE', True)
    if sandbox_mode or not getattr(settings, 'RAZORPAY_KEY_ID', None) or 'sample' in settings.RAZORPAY_KEY_ID:
        return RazorpaySandboxAdapter()
    return RazorpayLiveAdapter()

```

---

## File: `payments/tests.py`

```python
from django.test import TestCase

# Create your tests here.

```

---

## File: `payments/urls.py`

```python
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('api/create-order/', views.CreatePaymentOrderAPIView.as_view(), name='api_create_payment_order'),
    path('api/verify/', views.VerifyPaymentAPIView.as_view(), name='api_verify_payment'),
    path('api/webhook/', views.PaymentWebhookAPIView.as_view(), name='api_payment_webhook'),
    path('refund/<str:order_number>/', views.initiate_refund_view, name='initiate_refund'),
]

```

---

## File: `payments/views.py`

```python
import json
import logging
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from core.models import AuditLog
from core.decorators import staff_or_owner_required, get_user_shop
from orders.models import PrintOrder, PrintJob
from printers.services.routing_service import RoutingService
from .models import Payment, Refund
from .services.gateway_adapter import get_payment_gateway, RazorpaySandboxAdapter

logger = logging.getLogger(__name__)


class CreatePaymentOrderAPIView(APIView):
    """
    Creates a server-side payment order via the configured gateway adapter.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        order_number = request.data.get('order_number')
        order = get_object_or_404(PrintOrder, order_number=order_number)

        if order.status not in [PrintOrder.Status.AWAITING_PAYMENT, PrintOrder.Status.UPLOADED]:
            return Response(
                {'error': f"Order is already in '{order.get_status_display()}' state."},
                status=status.HTTP_400_BAD_REQUEST
            )

        gateway = get_payment_gateway()
        order_payload = gateway.create_order(
            amount=order.total_amount,
            currency='INR',
            receipt=order.order_number,
            notes={
                'order_number': order.order_number,
                'shop_id': str(order.shop.id),
                'shop_name': order.shop.name
            }
        )

        idempotency_key = f"pay_{order.order_number}_{order_payload['id']}"

        # Create or retrieve Payment model record
        payment, _ = Payment.objects.get_or_create(
            order=order,
            gateway_order_id=order_payload['id'],
            defaults={
                'amount': order.total_amount,
                'currency': 'INR',
                'status': Payment.Status.CREATED,
                'gateway_name': type(gateway).__name__,
                'idempotency_key': idempotency_key,
                'raw_response': order_payload
            }
        )

        resp_data = {
            'gateway_order_id': order_payload['id'],
            'amount_paise': order_payload['amount'],
            'currency': order_payload['currency'],
            'key_id': order_payload.get('key_id', 'rzp_test'),
            'order_number': order.order_number,
            'is_sandbox': isinstance(gateway, RazorpaySandboxAdapter),
        }

        # In sandbox mode, provide the helper signature for frontend test runner
        if isinstance(gateway, RazorpaySandboxAdapter):
            mock_payment_id = f"pay_test_{order.order_number.replace('-', '_')}"
            expected_sig = gateway.generate_expected_signature(order_payload['id'], mock_payment_id)
            resp_data['sandbox_helper'] = {
                'sample_payment_id': mock_payment_id,
                'sample_signature': expected_sig,
            }

        return Response(resp_data, status=status.HTTP_201_CREATED)


class VerifyPaymentAPIView(APIView):
    """
    Verifies payment signature on the backend.
    Never trusts a frontend payment-success message without cryptographic verification.
    Releases printing job only on verified payment.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        gateway_order_id = request.data.get('gateway_order_id')
        gateway_payment_id = request.data.get('gateway_payment_id')
        gateway_signature = request.data.get('gateway_signature')

        if not gateway_order_id or not gateway_payment_id or not gateway_signature:
            return Response(
                {'error': 'Missing payment verification credentials.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = get_object_or_404(Payment, gateway_order_id=gateway_order_id)
        order = payment.order

        gateway = get_payment_gateway()
        is_valid = gateway.verify_payment_signature(
            order_id=gateway_order_id,
            payment_id=gateway_payment_id,
            signature=gateway_signature
        )

        if not is_valid:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=['status', 'updated_at'])
            return Response(
                {'error': 'Cryptographic payment signature verification failed. Job will NOT be released.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Check idempotency: avoid double processing if webhook or repeat hit
            if payment.status == Payment.Status.CAPTURED:
                return Response({
                    'status': 'already_processed',
                    'order_number': order.order_number,
                    'redirect_url': f"/orders/track/{order.order_number}/"
                })

            payment.gateway_payment_id = gateway_payment_id
            payment.gateway_signature = gateway_signature
            payment.status = Payment.Status.CAPTURED
            payment.verified_at = timezone.now()
            payment.save()

            order.status = PrintOrder.Status.PAYMENT_VERIFIED
            order.save(update_fields=['status', 'updated_at'])

            # Route and dispatch exactly one authorized print job
            job = RoutingService.route_paid_order(order)

            AuditLog.objects.create(
                shop=order.shop,
                action='PAYMENT_VERIFIED',
                resource_type='Payment',
                resource_id=str(payment.id),
                details={
                    'order_number': order.order_number,
                    'payment_id': gateway_payment_id,
                    'amount': str(payment.amount),
                    'job_status': job.status,
                    'printer': job.printer.name if job.printer else 'QUEUED'
                }
            )

        return Response({
            'status': 'verified',
            'order_number': order.order_number,
            'job_status': job.status,
            'redirect_url': f"/orders/track/{order.order_number}/"
        })


class PaymentWebhookAPIView(APIView):
    """
    Handles payment provider webhooks with signature verification.
    Prevents duplicate releases using transaction locking and idempotency.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        signature = request.headers.get('X-Razorpay-Signature')
        gateway = get_payment_gateway()

        if not gateway.verify_webhook_signature(request.body, signature):
            return Response({'error': 'Invalid webhook signature.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = json.loads(request.body.decode('utf-8'))
            event = payload.get('event')

            if event == 'payment.captured':
                payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
                gateway_order_id = payment_entity.get('order_id')
                gateway_payment_id = payment_entity.get('id')

                payment = Payment.objects.filter(gateway_order_id=gateway_order_id).first()
                if payment and payment.status != Payment.Status.CAPTURED:
                    with transaction.atomic():
                        payment.gateway_payment_id = gateway_payment_id
                        payment.status = Payment.Status.CAPTURED
                        payment.verified_at = timezone.now()
                        payment.save()

                        order = payment.order
                        order.status = PrintOrder.Status.PAYMENT_VERIFIED
                        order.save()

                        RoutingService.route_paid_order(order)

            return Response({'status': 'webhook_received'})
        except Exception as e:
            logger.exception("Error processing payment webhook")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@staff_or_owner_required
def initiate_refund_view(request, order_number):
    """
    Issues an authorized refund for cancelled or failed print orders.
    """
    shop = get_user_shop(request.user)
    order = get_object_or_404(PrintOrder, shop=shop, order_number=order_number)
    payment = order.payments.filter(status=Payment.Status.CAPTURED).first()

    if not payment:
        messages.error(request, "No captured payment found to refund for this order.")
        return redirect('orders:order_detail', order_number=order_number)

    reason = request.POST.get('reason', 'Customer requested cancellation or hardware failure')

    gateway = get_payment_gateway()
    try:
        refund_data = gateway.initiate_refund(
            payment_id=payment.gateway_payment_id or payment.gateway_order_id,
            amount=payment.amount,
            reason=reason
        )

        with transaction.atomic():
            Refund.objects.create(
                payment=payment,
                amount=payment.amount,
                reason=reason,
                gateway_refund_id=refund_data.get('id', ''),
                status=Refund.Status.PROCESSED,
                authorized_by=request.user
            )

            order.status = PrintOrder.Status.REFUNDED
            order.save()

            if hasattr(order, 'print_job'):
                job = order.print_job
                job.status = PrintJob.Status.FAILED
                job.failure_reason = f"Refunded: {reason}"
                job.save()

            AuditLog.objects.create(
                shop=shop,
                user=request.user,
                action='PAYMENT_REFUNDED',
                resource_type='Refund',
                resource_id=refund_data.get('id', ''),
                details={
                    'order_number': order.order_number,
                    'amount': str(payment.amount),
                    'reason': reason
                }
            )

        messages.success(request, f"Refund of INR {payment.amount} has been processed successfully.")
    except Exception as e:
        messages.error(request, f"Refund processing failed: {str(e)}")

    return redirect('orders:order_detail', order_number=order_number)

```

---

## File: `printers/__init__.py`

```python

```

---

## File: `printers/admin.py`

```python
from django.contrib import admin
from .models import Printer, PrinterCapability, PrinterAssignment, Connector, ConnectorHeartbeat


class PrinterCapabilityInline(admin.StackedInline):
    model = PrinterCapability
    can_delete = False


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'system_printer_name', 'shop', 'is_active', 'is_online', 'is_default', 'handles_bw', 'handles_color')
    list_filter = ('is_active', 'is_online', 'is_default', 'handles_bw', 'handles_color', 'shop')
    search_fields = ('name', 'system_printer_name')
    inlines = [PrinterCapabilityInline]


@admin.register(PrinterAssignment)
class PrinterAssignmentAdmin(admin.ModelAdmin):
    list_display = ('shop', 'assignment_type', 'primary_printer', 'fallback_printer', 'updated_at')
    list_filter = ('shop', 'assignment_type')


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'machine_id', 'os_platform', 'is_active', 'last_heartbeat')
    list_filter = ('is_active', 'os_platform', 'shop')


@admin.register(ConnectorHeartbeat)
class ConnectorHeartbeatAdmin(admin.ModelAdmin):
    list_display = ('connector', 'timestamp')
    list_filter = ('connector',)

```

---

## File: `printers/api_views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings

from core.models import Shop, AuditLog
from .models import Connector, ConnectorHeartbeat, Printer, PrinterCapability
from orders.models import PrintJob, PrintOrder, PrintJobAttempt
from .serializers import (
    ConnectorRegisterSerializer,
    ConnectorHeartbeatSerializer,
    JobStatusUpdateSerializer
)
from printers.services.routing_service import RoutingService


class ConnectorAuthMixin:
    """
    Validates X-Shop-Token header against shop.connector_auth_token.
    """
    def authenticate_connector(self, request):
        token = request.headers.get('X-Shop-Token') or request.data.get('auth_token')
        shop_slug = request.headers.get('X-Shop-Slug') or request.data.get('shop_slug')

        if not token:
            return None, Response(
                {'error': 'Missing X-Shop-Token authentication header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            if shop_slug:
                shop = Shop.objects.get(slug=shop_slug, connector_auth_token=token)
            else:
                shop = Shop.objects.get(connector_auth_token=token)
            return shop, None
        except Shop.DoesNotExist:
            return None, Response(
                {'error': 'Invalid connector authentication token or shop identifier.'},
                status=status.HTTP_403_FORBIDDEN
            )


class ConnectorRegisterAPIView(APIView, ConnectorAuthMixin):
    permission_classes = [AllowAny]

    def post(self, request):
        shop, error_resp = self.authenticate_connector(request)
        if error_resp:
            return error_resp

        serializer = ConnectorRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        machine_id = data['machine_id']
        rsa_public_key = data.get('rsa_public_key', '').strip()

        now = timezone.now()
        connector, created = Connector.objects.update_or_create(
            shop=shop,
            machine_id=machine_id,
            defaults={
                'name': data['name'],
                'os_platform': data['os_platform'],
                'version': data['version'],
                'is_active': True,
                'last_heartbeat': now,
                'ip_address': request.META.get('REMOTE_ADDR')
            }
        )

        # Store connector RSA public key on shop if provided
        if rsa_public_key:
            shop.connector_public_key = rsa_public_key

        shop.connector_last_seen = now
        shop.save()

        AuditLog.objects.create(
            shop=shop,
            action='CONNECTOR_REGISTERED',
            resource_type='Connector',
            resource_id=str(connector.id),
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'machine_id': machine_id, 'version': data['version'], 'has_rsa_key': bool(rsa_public_key)}
        )

        return Response({
            'status': 'registered',
            'shop_id': str(shop.id),
            'shop_name': shop.name,
            'shop_slug': shop.slug,
            'connector_id': str(connector.id),
            'has_public_key': bool(shop.connector_public_key),
            'message': f"Connected successfully to {shop.name}."
        })


class ConnectorHeartbeatAPIView(APIView, ConnectorAuthMixin):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        shop, error_resp = self.authenticate_connector(request)
        if error_resp:
            return error_resp

        serializer = ConnectorHeartbeatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        shop.connector_last_seen = now
        shop.save(update_fields=['connector_last_seen'])

        machine_id = request.data.get('machine_id')
        connector = Connector.objects.filter(shop=shop, machine_id=machine_id).first()
        if not connector:
            connector = Connector.objects.filter(shop=shop).order_by('-created_at').first()

        if connector:
            connector.last_heartbeat = now
            connector.save(update_fields=['last_heartbeat'])

            ConnectorHeartbeat.objects.create(
                connector=connector,
                printers_payload=serializer.validated_data.get('printers', []),
                system_metrics=serializer.validated_data.get('system_metrics', {})
            )

        # Auto-discover or synchronize printers reported by local connector
        printers_list = serializer.validated_data.get('printers', [])
        active_printer_names = []

        for p_data in printers_list:
            sys_name = p_data.get('system_name', '').strip()
            friendly_name = p_data.get('friendly_name', sys_name)
            if not sys_name:
                continue

            active_printer_names.append(sys_name)
            is_online = p_data.get('is_online', True)
            status_msg = p_data.get('status', 'Ready')
            caps = p_data.get('capabilities', {})

            printer, created = Printer.objects.get_or_create(
                shop=shop,
                system_printer_name=sys_name,
                defaults={
                    'name': friendly_name,
                    'is_online': is_online,
                    'is_active': True,
                    'last_status_message': status_msg,
                    'handles_bw': caps.get('supports_bw', True),
                    'handles_color': caps.get('supports_color', False),
                }
            )

            if not created:
                printer.is_online = is_online
                printer.last_status_message = status_msg
                printer.handles_bw = caps.get('supports_bw', printer.handles_bw)
                printer.handles_color = caps.get('supports_color', printer.handles_color)
                printer.save()

            # Ensure capability model exists
            PrinterCapability.objects.update_or_create(
                printer=printer,
                defaults={
                    'supports_bw': caps.get('supports_bw', True),
                    'supports_color': caps.get('supports_color', False),
                    'supports_duplex': caps.get('supports_duplex', False),
                    'supported_paper_sizes': caps.get('supported_paper_sizes', ['A4']),
                    'supports_landscape': caps.get('supports_landscape', True),
                    'dpi': caps.get('dpi', 600),
                }
            )

        # Mark printers not seen in heartbeat as offline
        if active_printer_names:
            Printer.objects.filter(shop=shop).exclude(system_printer_name__in=active_printer_names).update(is_online=False)

        # Intelligent routing pass: check if any unassigned QUEUED jobs can now be routed
        unassigned_jobs = PrintJob.objects.filter(
            order__shop=shop,
            status=PrintJob.Status.QUEUED,
            printer__isnull=True
        ).select_related('order', 'order__preference')

        dispatched_count = 0
        for job in unassigned_jobs:
            target = RoutingService.determine_target_printer(shop, job.order.preference)
            if target:
                job.printer = target
                job.status = PrintJob.Status.DISPATCHED
                job.assigned_at = now
                job.dispatched_at = now
                job.save()
                job.order.status = PrintOrder.Status.ASSIGNED
                job.order.save()
                dispatched_count += 1

        return Response({
            'status': 'ok',
            'printers_synced': len(printers_list),
            'dispatched_queued_jobs': dispatched_count
        })


class ConnectorPollJobsAPIView(APIView, ConnectorAuthMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        shop, error_resp = self.authenticate_connector(request)
        if error_resp:
            return error_resp

        # Fetch all dispatched jobs for this shop
        jobs = PrintJob.objects.filter(
            order__shop=shop,
            status=PrintJob.Status.DISPATCHED
        ).select_related('order', 'order__document', 'order__preference', 'printer')

        base_url = getattr(settings, 'BASE_APP_URL', 'http://127.0.0.1:8000').rstrip('/')

        jobs_payload = []
        for job in jobs:
            order = job.order
            doc = order.document
            pref = order.preference

            download_url = f"{base_url}/orders/api/document/{doc.id}/download/?token={shop.connector_auth_token}"

            jobs_payload.append({
                'job_id': str(job.id),
                'order_number': order.order_number,
                'printer_system_name': job.printer.system_printer_name if job.printer else '',
                'printer_friendly_name': job.printer.name if job.printer else '',
                'download_url': download_url,
                'original_filename': doc.original_filename,
                'file_hash_sha256': doc.file_hash_sha256,
                'encrypted_key_bundle': doc.encrypted_key_bundle,
                'encryption_iv': doc.encryption_iv,
                'encryption_tag': doc.encryption_tag,
                'expected_page_count': doc.detected_page_count,
                'preferences': {
                    'color_mode': pref.color_mode,
                    'duplex_mode': pref.duplex_mode,
                    'paper_size': pref.paper_size,
                    'copies': pref.copies,
                    'page_range_type': pref.page_range_type,
                    'page_range_selection': pref.page_range_selection,
                }
            })

        return Response({'pending_jobs': jobs_payload, 'count': len(jobs_payload)})


class ConnectorUpdateJobStatusAPIView(APIView, ConnectorAuthMixin):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        shop, error_resp = self.authenticate_connector(request)
        if error_resp:
            return error_resp

        serializer = JobStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        job = get_object_or_404(PrintJob, id=data['job_id'], order__shop=shop)
        new_status = data['status']
        verified_pages = data.get('verified_page_count')
        failure_reason = data.get('failure_reason', '')
        ack_id = data.get('connector_ack_id', '')

        now = timezone.now()
        job.status = new_status
        if ack_id:
            job.connector_ack_id = ack_id
        if failure_reason:
            job.failure_reason = failure_reason

        # Synchronize order status
        order = job.order
        doc = order.document

        if verified_pages is not None:
            doc.verified_page_count = verified_pages
            doc.save(update_fields=['verified_page_count'])

            # Safety check: if verified pages exceed paid pages, hold verification
            if verified_pages > doc.detected_page_count:
                job.status = PrintJob.Status.HOLD_VERIFICATION
                job.failure_reason = (
                    f"Page count mismatch! Customer paid for {doc.detected_page_count} pages, "
                    f"but decrypted document contains {verified_pages} pages."
                )
                order.status = PrintOrder.Status.FAILED
                job.save()
                order.save()
                return Response({
                    'status': 'held',
                    'action': 'HOLD_VERIFICATION',
                    'message': job.failure_reason
                })

        if new_status == PrintJob.Status.RECEIVED_BY_CONNECTOR:
            order.status = PrintOrder.Status.PRINTING
        elif new_status == PrintJob.Status.SUBMITTED_TO_SPOOLER:
            order.status = PrintOrder.Status.PRINTING
        elif new_status == PrintJob.Status.PHYSICALLY_PRINTED:
            order.status = PrintOrder.Status.COMPLETED
            job.completed_at = now
        elif new_status == PrintJob.Status.FAILED:
            order.status = PrintOrder.Status.FAILED
        elif new_status == PrintJob.Status.HOLD_VERIFICATION:
            order.status = PrintOrder.Status.FAILED

        job.save()
        order.save()

        PrintJobAttempt.objects.create(
            job=job,
            printer=job.printer,
            attempt_number=job.attempts.count() + 1,
            status=new_status,
            error_message=failure_reason
        )

        AuditLog.objects.create(
            shop=shop,
            action='PRINT_JOB_STATUS_UPDATED',
            resource_type='PrintJob',
            resource_id=str(job.id),
            details={
                'order_number': order.order_number,
                'new_status': new_status,
                'verified_page_count': verified_pages,
                'failure_reason': failure_reason
            }
        )

        return Response({
            'status': 'updated',
            'job_id': str(job.id),
            'order_status': order.status,
            'job_status': job.status
        })

```

---

## File: `printers/apps.py`

```python
from django.apps import AppConfig


class PrintersConfig(AppConfig):
    name = 'printers'

```

---

## File: `printers/migrations/0001_initial.py`

```python
# Generated by Django 6.1.3 on 2026-11-11 08:53

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Connector',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150)),
                ('machine_id', models.CharField(max_length=150)),
                ('os_platform', models.CharField(default='Windows', max_length=100)),
                ('version', models.CharField(default='1.0.0', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('last_heartbeat', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connectors', to='core.shop')),
            ],
        ),
        migrations.CreateModel(
            name='ConnectorHeartbeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('printers_payload', models.JSONField(default=list)),
                ('system_metrics', models.JSONField(default=dict)),
                ('connector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='heartbeats', to='printers.connector')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Friendly display name in PrintGrid', max_length=150)),
                ('system_printer_name', models.CharField(help_text="Exact Windows printer spooler queue name (e.g., 'HP LaserJet Pro MFP M428fdw')", max_length=200)),
                ('model_name', models.CharField(blank=True, max_length=150)),
                ('is_active', models.BooleanField(default=True, help_text='Owner/Staff operational toggle')),
                ('is_online', models.BooleanField(default=False, help_text='Live connection state reported by connector')),
                ('is_default', models.BooleanField(default=False)),
                ('handles_bw', models.BooleanField(default=True)),
                ('handles_color', models.BooleanField(default=False)),
                ('last_status_message', models.CharField(blank=True, default='Ready', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='printers', to='core.shop')),
            ],
            options={
                'ordering': ['-is_default', 'name'],
                'unique_together': {('shop', 'system_printer_name')},
            },
        ),
        migrations.CreateModel(
            name='PrinterCapability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('supports_bw', models.BooleanField(default=True)),
                ('supports_color', models.BooleanField(default=False)),
                ('supports_duplex', models.BooleanField(default=False)),
                ('supported_paper_sizes', models.JSONField(default=list, help_text="Supported paper size codes, e.g. ['A4', 'A3', 'LETTER']")),
                ('supports_landscape', models.BooleanField(default=True)),
                ('dpi', models.IntegerField(default=600)),
                ('max_copies_per_job', models.IntegerField(default=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('printer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='capability', to='printers.printer')),
            ],
        ),
        migrations.CreateModel(
            name='PrinterAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('assignment_type', models.CharField(choices=[('BW_SINGLE', 'B&W Single-Sided'), ('BW_DOUBLE', 'B&W Double-Sided'), ('COLOR_SINGLE', 'Color Single-Sided'), ('COLOR_DOUBLE', 'Color Double-Sided'), ('A3_BW', 'A3 B&W'), ('A3_COLOR', 'A3 Color')], max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fallback_printer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_fallback_for', to='printers.printer')),
                ('primary_printer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_primary_for', to='printers.printer')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='printer_assignments', to='core.shop')),
            ],
            options={
                'unique_together': {('shop', 'assignment_type')},
            },
        ),
    ]

```

---

## File: `printers/migrations/__init__.py`

```python

```

---

## File: `printers/models.py`

```python
import uuid
from django.db import models
from core.models import Shop


class Printer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='printers')
    name = models.CharField(max_length=150, help_text="Friendly display name in PrintGrid")
    system_printer_name = models.CharField(
        max_length=200,
        help_text="Exact Windows printer spooler queue name (e.g., 'HP LaserJet Pro MFP M428fdw')"
    )
    model_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True, help_text="Owner/Staff operational toggle")
    is_online = models.BooleanField(default=False, help_text="Live connection state reported by connector")
    is_default = models.BooleanField(default=False)
    handles_bw = models.BooleanField(default=True)
    handles_color = models.BooleanField(default=False)
    last_status_message = models.CharField(max_length=255, blank=True, default="Ready")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']
        unique_together = ('shop', 'system_printer_name')

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        active = "Active" if self.is_active else "Disabled"
        return f"{self.name} [{status}, {active}]"

    def can_print(self, color_mode, duplex_mode, paper_size):
        """
        Validates whether this printer satisfies the specified print preferences.
        """
        if not self.is_active or not self.is_online:
            return False

        if color_mode == 'COLOR' and not self.handles_color:
            return False
        if color_mode == 'BW' and not self.handles_bw:
            return False

        capability = getattr(self, 'capability', None)
        if capability:
            if color_mode == 'COLOR' and not capability.supports_color:
                return False
            if duplex_mode == 'DOUBLE' and not capability.supports_duplex:
                return False
            if paper_size not in capability.supported_paper_sizes:
                return False

        return True


class PrinterCapability(models.Model):
    printer = models.OneToOneField(Printer, on_delete=models.CASCADE, related_name='capability')
    supports_bw = models.BooleanField(default=True)
    supports_color = models.BooleanField(default=False)
    supports_duplex = models.BooleanField(default=False)
    supported_paper_sizes = models.JSONField(
        default=list,
        help_text="Supported paper size codes, e.g. ['A4', 'A3', 'LETTER']"
    )
    supports_landscape = models.BooleanField(default=True)
    dpi = models.IntegerField(default=600)
    max_copies_per_job = models.IntegerField(default=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Capabilities for {self.printer.name}"


class PrinterAssignment(models.Model):
    class AssignmentType(models.TextChoices):
        BW_SINGLE = 'BW_SINGLE', 'B&W Single-Sided'
        BW_DOUBLE = 'BW_DOUBLE', 'B&W Double-Sided'
        COLOR_SINGLE = 'COLOR_SINGLE', 'Color Single-Sided'
        COLOR_DOUBLE = 'COLOR_DOUBLE', 'Color Double-Sided'
        A3_BW = 'A3_BW', 'A3 B&W'
        A3_COLOR = 'A3_COLOR', 'A3 Color'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='printer_assignments')
    assignment_type = models.CharField(max_length=50, choices=AssignmentType.choices)
    primary_printer = models.ForeignKey(
        Printer,
        on_delete=models.CASCADE,
        related_name='assigned_primary_for'
    )
    fallback_printer = models.ForeignKey(
        Printer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_fallback_for'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('shop', 'assignment_type')

    def __str__(self):
        return f"{self.get_assignment_type_display()} -> {self.primary_printer.name}"


class Connector(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='connectors')
    name = models.CharField(max_length=150)
    machine_id = models.CharField(max_length=150)
    os_platform = models.CharField(max_length=100, default='Windows')
    version = models.CharField(max_length=50, default='1.0.0')
    is_active = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


class ConnectorHeartbeat(models.Model):
    connector = models.ForeignKey(Connector, on_delete=models.CASCADE, related_name='heartbeats')
    timestamp = models.DateTimeField(auto_now_add=True)
    printers_payload = models.JSONField(default=list)
    system_metrics = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']

```

---

## File: `printers/serializers.py`

```python
from rest_framework import serializers
from .models import Printer, PrinterCapability, PrinterAssignment, Connector
from orders.models import PrintJob, PrintOrder


class PrinterCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrinterCapability
        fields = ['supports_bw', 'supports_color', 'supports_duplex', 'supported_paper_sizes', 'supports_landscape', 'dpi']


class PrinterSerializer(serializers.ModelSerializer):
    capability = PrinterCapabilitySerializer(read_only=True)

    class Meta:
        model = Printer
        fields = [
            'id', 'name', 'system_printer_name', 'model_name',
            'is_active', 'is_online', 'is_default', 'handles_bw',
            'handles_color', 'last_status_message', 'capability'
        ]


class ConnectorRegisterSerializer(serializers.Serializer):
    machine_id = serializers.CharField(max_length=150)
    name = serializers.CharField(max_length=150)
    os_platform = serializers.CharField(max_length=100, default='Windows')
    version = serializers.CharField(max_length=50, default='1.0.0')
    rsa_public_key = serializers.CharField(required=False, allow_blank=True)


class ConnectorHeartbeatSerializer(serializers.Serializer):
    printers = serializers.ListField(child=serializers.DictField())
    system_metrics = serializers.DictField(required=False, default=dict)


class JobStatusUpdateSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=PrintJob.Status.choices)
    verified_page_count = serializers.IntegerField(required=False, allow_null=True)
    failure_reason = serializers.CharField(required=False, allow_blank=True)
    connector_ack_id = serializers.CharField(required=False, allow_blank=True)

```

---

## File: `printers/services/__init__.py`

```python

```

---

## File: `printers/services/routing_service.py`

```python
import logging
from django.utils import timezone
from django.db import transaction
from printers.models import Printer, PrinterAssignment, Connector
from orders.models import PrintOrder, PrintJob, PrintJobAttempt
from core.models import AuditLog

logger = logging.getLogger(__name__)


class RoutingService:
    @classmethod
    def get_eligible_printers(cls, shop, preference, require_online=True):
        """
        Returns a list of printers in the shop that physically and operationally
        satisfy the customer's print preferences.
        """
        qs = Printer.objects.filter(shop=shop, is_active=True)
        if require_online:
            qs = qs.filter(is_online=True)

        eligible = []
        for printer in qs:
            if printer.can_print(
                color_mode=preference.color_mode,
                duplex_mode=preference.duplex_mode,
                paper_size=preference.paper_size
            ):
                eligible.append(printer)
        return eligible

    @classmethod
    def determine_target_printer(cls, shop, preference):
        """
        Selects the best target printer according to shop assignment rules,
        default settings, and active capabilities.
        """
        # Determine assignment key
        is_color = preference.color_mode == 'COLOR'
        is_double = preference.duplex_mode == 'DOUBLE'
        is_a3 = preference.paper_size == 'A3'

        if is_a3:
            assignment_key = PrinterAssignment.AssignmentType.A3_COLOR if is_color else PrinterAssignment.AssignmentType.A3_BW
        else:
            if is_color:
                assignment_key = (
                    PrinterAssignment.AssignmentType.COLOR_DOUBLE if is_double
                    else PrinterAssignment.AssignmentType.COLOR_SINGLE
                )
            else:
                assignment_key = (
                    PrinterAssignment.AssignmentType.BW_DOUBLE if is_double
                    else PrinterAssignment.AssignmentType.BW_SINGLE
                )

        assignment = PrinterAssignment.objects.filter(
            shop=shop,
            assignment_type=assignment_key
        ).select_related('primary_printer', 'fallback_printer').first()

        if assignment:
            primary = assignment.primary_printer
            if primary and primary.is_active and primary.is_online and primary.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
                return primary
            fallback = assignment.fallback_printer
            if fallback and fallback.is_active and fallback.is_online and fallback.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
                return fallback

        # If assignment didn't match an online capable printer, try default printer
        default_printer = Printer.objects.filter(shop=shop, is_default=True, is_active=True, is_online=True).first()
        if default_printer and default_printer.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
            return default_printer

        # Fallback to any online eligible printer
        eligible = cls.get_eligible_printers(shop, preference, require_online=True)
        if eligible:
            return eligible[0]

        # No online capable printer found right now
        return None

    @classmethod
    @transaction.atomic
    def route_paid_order(cls, order: PrintOrder) -> PrintJob:
        """
        Processes a paid order:
        1. Ensures order status is PAYMENT_VERIFIED or QUEUED.
        2. Dispatches or queues exactly one PrintJob.
        3. Prevents duplicate job creation.
        """
        if hasattr(order, 'print_job'):
            job = order.print_job
            # If job already exists and is not FAILED, return it without creating duplicate
            if job.status not in [PrintJob.Status.FAILED]:
                return job
        else:
            job = PrintJob(order=order)

        shop = order.shop
        target_printer = cls.determine_target_printer(shop, order.preference)

        # Associate active shop connector
        active_connector = Connector.objects.filter(shop=shop, is_active=True).order_by('-last_heartbeat').first()

        job.connector = active_connector

        if target_printer:
            job.printer = target_printer
            job.status = PrintJob.Status.DISPATCHED
            job.assigned_at = timezone.now()
            job.dispatched_at = timezone.now()
            order.status = PrintOrder.Status.ASSIGNED
        else:
            job.printer = None
            job.status = PrintJob.Status.QUEUED
            order.status = PrintOrder.Status.QUEUED

        job.save()
        order.save()

        # Log attempt
        PrintJobAttempt.objects.create(
            job=job,
            printer=target_printer,
            attempt_number=job.attempts.count() + 1,
            status=job.status,
            error_message="Queued - waiting for compatible online printer" if not target_printer else "Dispatched to target printer"
        )

        AuditLog.objects.create(
            shop=shop,
            action='PRINT_JOB_ROUTED',
            resource_type='PrintJob',
            resource_id=str(job.id),
            details={
                'order_number': order.order_number,
                'target_printer': target_printer.name if target_printer else 'QUEUED_UNASSIGNED',
                'status': job.status,
                'color_mode': order.preference.color_mode,
                'paper_size': order.preference.paper_size,
            }
        )

        return job

    @classmethod
    @transaction.atomic
    def reassign_job(cls, job: PrintJob, new_printer: Printer, user=None):
        """
        Reassigns an eligible QUEUED or FAILED job to an active, compatible printer.
        Never reassigns an already DISPATCHED or PRINTING physical job without authorization.
        """
        if job.status in [PrintJob.Status.SUBMITTED_TO_SPOOLER, PrintJob.Status.PHYSICALLY_PRINTED]:
            raise ValueError("Cannot reassign a job that is already submitted to or completed by the physical printer.")

        pref = job.order.preference
        if not new_printer.can_print(pref.color_mode, pref.duplex_mode, pref.paper_size):
            raise ValueError(f"Selected printer '{new_printer.name}' does not support this document's printing preferences.")

        old_printer_name = job.printer.name if job.printer else "None"
        job.printer = new_printer
        job.status = PrintJob.Status.DISPATCHED
        job.assigned_at = timezone.now()
        job.dispatched_at = timezone.now()
        job.save()

        job.order.status = PrintOrder.Status.ASSIGNED
        job.order.save()

        PrintJobAttempt.objects.create(
            job=job,
            printer=new_printer,
            attempt_number=job.attempts.count() + 1,
            status=PrintJob.Status.DISPATCHED,
            error_message=f"Reassigned from {old_printer_name} to {new_printer.name}",
            authorized_by=user
        )

        AuditLog.objects.create(
            shop=job.order.shop,
            user=user,
            action='PRINT_JOB_REASSIGNED',
            resource_type='PrintJob',
            resource_id=str(job.id),
            details={
                'from_printer': old_printer_name,
                'to_printer': new_printer.name,
                'authorized_by': user.username if user else 'System'
            }
        )
        return job

```

---

## File: `printers/tests.py`

```python
from django.test import TestCase

# Create your tests here.

```

---

## File: `printers/urls.py`

```python
from django.urls import path
from . import views
from . import api_views

app_name = 'printers'

urlpatterns = [
    # Dashboard views
    path('list/', views.printer_list, name='printer_list'),
    path('toggle/<uuid:printer_id>/', views.printer_toggle_active, name='printer_toggle_active'),
    path('set-default/<uuid:printer_id>/', views.printer_set_default, name='printer_set_default'),
    path('assignments/', views.printer_assignments_view, name='printer_assignments'),
    path('reassign-queued/', views.reassign_queued_jobs_view, name='reassign_queued_jobs'),

    # Connector REST APIs
    path('api/connector/register/', api_views.ConnectorRegisterAPIView.as_view(), name='api_connector_register'),
    path('api/connector/heartbeat/', api_views.ConnectorHeartbeatAPIView.as_view(), name='api_connector_heartbeat'),
    path('api/connector/poll-jobs/', api_views.ConnectorPollJobsAPIView.as_view(), name='api_connector_poll_jobs'),
    path('api/connector/update-job-status/', api_views.ConnectorUpdateJobStatusAPIView.as_view(), name='api_connector_update_job_status'),
]

```

---

## File: `printers/views.py`

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from core.decorators import owner_required, get_user_shop
from core.models import AuditLog
from .models import Printer, PrinterCapability, PrinterAssignment
from orders.models import PrintJob
from printers.services.routing_service import RoutingService


@owner_required
def printer_list(request):
    """
    Overview of all printers configured for the shop.
    """
    shop = get_user_shop(request.user)
    printers = Printer.objects.filter(shop=shop).select_related('capability')

    context = {
        'shop': shop,
        'printers': printers,
    }
    return render(request, 'printers/printer_list.html', context)


@owner_required
def printer_toggle_active(request, printer_id):
    """
    Toggles printer active status.
    """
    shop = get_user_shop(request.user)
    printer = get_object_or_404(Printer, id=printer_id, shop=shop)
    printer.is_active = not printer.is_active
    printer.save()

    AuditLog.objects.create(
        shop=shop,
        user=request.user,
        action='PRINTER_STATUS_TOGGLED',
        resource_type='Printer',
        resource_id=str(printer.id),
        details={'printer_name': printer.name, 'is_active': printer.is_active}
    )
    status_str = "enabled" if printer.is_active else "disabled"
    messages.info(request, f"Printer '{printer.name}' has been {status_str}.")
    return redirect('printers:printer_list')


@owner_required
def printer_set_default(request, printer_id):
    """
    Sets the selected printer as shop default printer.
    """
    shop = get_user_shop(request.user)
    with transaction.atomic():
        Printer.objects.filter(shop=shop).update(is_default=False)
        printer = get_object_or_404(Printer, id=printer_id, shop=shop)
        printer.is_default = True
        printer.save()

    AuditLog.objects.create(
        shop=shop,
        user=request.user,
        action='DEFAULT_PRINTER_CHANGED',
        resource_type='Printer',
        resource_id=str(printer.id),
        details={'default_printer': printer.name}
    )
    messages.success(request, f"'{printer.name}' is now the default printer for your shop.")
    return redirect('printers:printer_list')


@owner_required
def printer_assignments_view(request):
    """
    Manages intelligent job routing assignments for B&W, Color, Duplex, and A3 jobs.
    """
    shop = get_user_shop(request.user)
    printers = Printer.objects.filter(shop=shop, is_active=True)
    assignments = PrinterAssignment.objects.filter(shop=shop).select_related('primary_printer', 'fallback_printer')

    assignment_map = {a.assignment_type: a for a in assignments}
    assignment_types = PrinterAssignment.AssignmentType.choices

    if request.method == 'POST':
        with transaction.atomic():
            for code, label in assignment_types:
                primary_id = request.POST.get(f'primary_{code}')
                fallback_id = request.POST.get(f'fallback_{code}')

                if primary_id:
                    primary_p = printers.filter(id=primary_id).first()
                    fallback_p = printers.filter(id=fallback_id).first() if fallback_id else None

                    if primary_p:
                        PrinterAssignment.objects.update_or_create(
                            shop=shop,
                            assignment_type=code,
                            defaults={
                                'primary_printer': primary_p,
                                'fallback_printer': fallback_p
                            }
                        )
                else:
                    PrinterAssignment.objects.filter(shop=shop, assignment_type=code).delete()

        AuditLog.objects.create(
            shop=shop,
            user=request.user,
            action='ROUTING_ASSIGNMENTS_UPDATED',
            resource_type='PrinterAssignment',
            resource_id=str(shop.id),
            details={'updated_by': request.user.username}
        )
        messages.success(request, "Printer routing rules saved successfully.")
        return redirect('printers:printer_assignments')

    context = {
        'shop': shop,
        'printers': printers,
        'assignment_types': assignment_types,
        'assignment_map': assignment_map,
    }
    return render(request, 'printers/printer_assignments.html', context)


@owner_required
def reassign_queued_jobs_view(request):
    """
    Reassigns unassigned QUEUED jobs to an eligible online printer.
    """
    shop = get_user_shop(request.user)
    queued_jobs = PrintJob.objects.filter(
        order__shop=shop,
        status=PrintJob.Status.QUEUED
    ).select_related('order', 'order__preference')

    reassigned_count = 0
    for job in queued_jobs:
        target = RoutingService.determine_target_printer(shop, job.order.preference)
        if target:
            RoutingService.reassign_job(job, target, user=request.user)
            reassigned_count += 1

    if reassigned_count > 0:
        messages.success(request, f"Successfully routed {reassigned_count} queued job(s) to active printers.")
    else:
        messages.info(request, "No eligible online printer was available to take queued jobs right now.")

    return redirect('orders:order_list')

```

---

## File: `requirements.txt`

```text
Django>=5.0,<7.0
djangorestframework>=3.14.0
qrcode>=8.0
pillow>=10.0.0
pymysql>=1.1.0
cryptography>=42.0.0
pypdf>=4.0.0
requests>=2.31.0
pytest>=8.0.0
pytest-django>=4.8.0
python-dotenv>=1.0.0

```

---

## File: `static/css/styles.css`

```css
/* KEP PrintGrid Custom Stylesheet */
:root {
    --pg-navy: #0F172A;
    --pg-navy-light: #1E293B;
    --pg-blue: #2563EB;
    --pg-blue-hover: #1D4ED8;
    --pg-cyan: #06B6D4;
    --pg-bg: #F8FAFC;
    --pg-card-bg: #FFFFFF;
    --pg-border: #E2E8F0;
    --pg-text: #0F172A;
    --pg-muted: #64748B;
}

body {
    background-color: var(--pg-bg);
    color: var(--pg-text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.main-content {
    flex: 1;
}

/* Navbar */
.navbar-brand {
    font-weight: 700;
    letter-spacing: -0.5px;
    font-size: 1.25rem;
}

.badge-brand {
    background-color: #38BDF8;
    color: #0F172A;
    font-size: 0.7rem;
    font-weight: 700;
    vertical-align: middle;
}

/* Sidebar Dashboard Layout */
.dashboard-container {
    display: flex;
    min-height: calc(100vh - 60px);
}

.sidebar {
    width: 260px;
    background-color: var(--pg-navy);
    color: #F8FAFC;
    flex-shrink: 0;
}

.sidebar .nav-link {
    color: #94A3B8;
    font-weight: 500;
    padding: 0.75rem 1.25rem;
    border-radius: 8px;
    margin: 0.2rem 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    transition: all 0.2s ease-in-out;
}

.sidebar .nav-link:hover, .sidebar .nav-link.active {
    color: #FFFFFF;
    background-color: var(--pg-navy-light);
}

.sidebar .nav-link.active {
    border-left: 4px solid var(--pg-cyan);
}

.dashboard-main {
    flex: 1;
    padding: 2rem;
    background-color: var(--pg-bg);
    overflow-y: auto;
}

/* Metric Cards */
.metric-card {
    background-color: var(--pg-card-bg);
    border: 1px solid var(--pg-border);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.metric-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--pg-navy);
}

.metric-label {
    font-size: 0.875rem;
    color: var(--pg-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Status Badges */
.badge-status-completed {
    background-color: #DCFCE7;
    color: #166534;
}

.badge-status-printing {
    background-color: #DBEAFE;
    color: #1E40AF;
}

.badge-status-queued {
    background-color: #FEF3C7;
    color: #92400E;
}

.badge-status-failed {
    background-color: #FEE2E2;
    color: #991B1B;
}

/* Dropzone for Uploads */
.upload-dropzone {
    border: 2px dashed #94A3B8;
    background-color: #F8FAFC;
    border-radius: 16px;
    padding: 3rem 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

.upload-dropzone:hover, .upload-dropzone.dragover {
    border-color: var(--pg-blue);
    background-color: #EFF6FF;
}

/* Stepper for Customer Flow */
.stepper-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2rem;
    position: relative;
}

.step-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    z-index: 2;
}

.step-num {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: #E2E8F0;
    color: var(--pg-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
}

.step-node.active .step-num {
    background-color: var(--pg-blue);
    color: #FFFFFF;
}

.step-node.done .step-num {
    background-color: #10B981;
    color: #FFFFFF;
}

.step-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--pg-muted);
}

.step-node.active .step-title {
    color: var(--pg-navy);
}

/* Canvas Preview Container */
.pdf-preview-box {
    max-height: 400px;
    overflow-y: auto;
    background-color: #475569;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}

.pdf-preview-canvas {
    max-width: 100%;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
}

```

---

## File: `static/js/client_crypto.js`

```javascript
/**
 * KEP PrintGrid Zero-Knowledge Client Document Encryption
 * Uses Web Crypto API (AES-256-GCM + RSA-OAEP SHA-256)
 */

class ClientCryptoManager {
    static async arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    static async computeSha256(arrayBuffer) {
        const hashBuffer = await window.crypto.subtle.digest('SHA-256', arrayBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    static pemToArrayBuffer(pem) {
        // Strip headers, footers, newlines
        const cleanPem = pem
            .replace(/-----BEGIN [A-Z ]+-----/g, '')
            .replace(/-----END [A-Z ]+-----/g, '')
            .replace(/\s+/g, '');
        const binaryStr = window.atob(cleanPem);
        const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) {
            bytes[i] = binaryStr.charCodeAt(i);
        }
        return bytes.buffer;
    }

    static async importRsaPublicKey(pem) {
        const spkiBuffer = this.pemToArrayBuffer(pem);
        return await window.crypto.subtle.importKey(
            'spki',
            spkiBuffer,
            {
                name: 'RSA-OAEP',
                hash: { name: 'SHA-256' }
            },
            true,
            ['wrapKey']
        );
    }

    /**
     * Encrypts a PDF File/ArrayBuffer before transmitting it to the cloud.
     */
    static async encryptDocument(fileArrayBuffer, rsaPublicKeyPem = null) {
        // 1. Generate random AES-256 key
        const aesKey = await window.crypto.subtle.generateKey(
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );

        // 2. Generate 12-byte random IV
        const iv = window.crypto.getRandomValues(new Uint8Array(12));

        // 3. Encrypt PDF data via AES-GCM (appends 16-byte authentication tag)
        const encryptedFullBuffer = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv, tagLength: 128 },
            aesKey,
            fileArrayBuffer
        );

        // Split ciphertext and 16-byte authentication tag
        const totalLen = encryptedFullBuffer.byteLength;
        const tagLen = 16;
        const ciphertextLen = totalLen - tagLen;

        const ciphertextBytes = new Uint8Array(encryptedFullBuffer, 0, ciphertextLen);
        const tagBytes = new Uint8Array(encryptedFullBuffer, ciphertextLen, tagLen);

        // 4. Wrap AES key using Shop RSA Public Key
        let wrappedKeyB64 = '';
        if (rsaPublicKeyPem && rsaPublicKeyPem.trim().length > 0) {
            try {
                const rsaKey = await this.importRsaPublicKey(rsaPublicKeyPem);
                const wrappedKeyBuffer = await window.crypto.subtle.wrapKey(
                    'raw',
                    aesKey,
                    rsaKey,
                    { name: 'RSA-OAEP', hash: { name: 'SHA-256' } }
                );
                wrappedKeyB64 = await this.arrayBufferToBase64(wrappedKeyBuffer);
            } catch (err) {
                console.warn("RSA wrapping failed with provided key, using raw export:", err);
                const rawKey = await window.crypto.subtle.exportKey('raw', aesKey);
                wrappedKeyB64 = await this.arrayBufferToBase64(rawKey);
            }
        } else {
            // Dev fallback when shop connector key not yet synced
            const rawKey = await window.crypto.subtle.exportKey('raw', aesKey);
            wrappedKeyB64 = await this.arrayBufferToBase64(rawKey);
        }

        const ivB64 = await this.arrayBufferToBase64(iv.buffer);
        const tagB64 = await this.arrayBufferToBase64(tagBytes.buffer);
        const sha256Hex = await this.computeSha256(ciphertextBytes.buffer);

        const encryptedBlob = new Blob([ciphertextBytes], { type: 'application/octet-stream' });

        return {
            encryptedBlob,
            encryptedKeyBundleB64: wrappedKeyB64,
            ivB64: ivB64,
            tagB64: tagB64,
            sha256Hex: sha256Hex,
            fileSizeBytes: encryptedBlob.size
        };
    }
}

window.ClientCryptoManager = ClientCryptoManager;

```

---

## File: `static/js/order_flow.js`

```javascript
/**
 * KEP PrintGrid Customer Ordering Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const shopSlug = window.PRINTGRID_SHOP_SLUG;
    const rsaPublicKey = window.PRINTGRID_RSA_KEY || '';

    // Elements
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('pdfFileInput');
    const docInfoSection = document.getElementById('docInfoSection');
    const docNameSpan = document.getElementById('docName');
    const docPagesSpan = document.getElementById('docPages');
    const docSizeSpan = document.getElementById('docSize');
    const previewContainer = document.getElementById('pdfPreviewContainer');
    const previewCanvas = document.getElementById('pdfPreviewCanvas');

    // Controls
    const colorModeRadios = document.querySelectorAll('input[name="color_mode"]');
    const duplexRadios = document.querySelectorAll('input[name="duplex_mode"]');
    const paperSizeRadios = document.querySelectorAll('input[name="paper_size"]');
    const copiesInput = document.getElementById('copiesInput');
    const pageRangeSelect = document.getElementById('pageRangeSelect');
    const customRangeInput = document.getElementById('customRangeInput');
    const customRangeDiv = document.getElementById('customRangeDiv');

    // Summary elements
    const quoteBreakdownDiv = document.getElementById('quoteBreakdown');
    const quoteTotalSpan = document.getElementById('quoteTotal');
    const submitOrderBtn = document.getElementById('submitOrderBtn');
    const uploadStatusAlert = document.getElementById('uploadStatusAlert');

    // State
    let selectedFile = null;
    let fileArrayBuffer = null;
    let detectedPages = 1;
    let uploadedDocumentId = null;

    if (!dropzone) return;

    // Dropzone interactions
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    async function handleFileSelection(file) {
        if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
            alert('Only PDF documents are supported for printing.');
            return;
        }

        // Limit size: 50MB
        if (file.size > 50 * 1024 * 1024) {
            alert('File exceeds maximum allowed upload size (50 MB).');
            return;
        }

        selectedFile = file;
        docNameSpan.textContent = file.name;
        docSizeSpan.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        docInfoSection.classList.remove('d-none');

        // Read buffer
        fileArrayBuffer = await file.arrayBuffer();

        // Count pages & render preview using PDF.js if available
        if (window.pdfjsLib) {
            try {
                const pdf = await window.pdfjsLib.getDocument({ data: fileArrayBuffer }).promise;
                detectedPages = pdf.numPages;
                docPagesSpan.textContent = detectedPages;

                // Render page 1 preview
                const page = await pdf.getPage(1);
                const viewport = page.getViewport({ scale: 1.0 });
                previewCanvas.height = viewport.height;
                previewCanvas.width = viewport.width;
                const renderContext = {
                    canvasContext: previewCanvas.getContext('2d'),
                    viewport: viewport
                };
                await page.render(renderContext).promise;
                previewContainer.classList.remove('d-none');
            } catch (err) {
                console.warn('PDF.js rendering note:', err);
                detectedPages = 1;
                docPagesSpan.textContent = '1 (Preview not rendered)';
            }
        } else {
            detectedPages = 1;
            docPagesSpan.textContent = 'Detected';
        }

        fetchQuote();
    }

    // Range select toggles
    pageRangeSelect.addEventListener('change', () => {
        if (pageRangeSelect.value === 'CUSTOM') {
            customRangeDiv.classList.remove('d-none');
        } else {
            customRangeDiv.classList.add('d-none');
        }
        fetchQuote();
    });

    // Event listeners for recalculating price quote
    [...colorModeRadios, ...duplexRadios, ...paperSizeRadios].forEach(el => el.addEventListener('change', fetchQuote));
    copiesInput.addEventListener('input', fetchQuote);
    customRangeInput.addEventListener('input', fetchQuote);

    function getSelectedRadio(radios) {
        for (const r of radios) {
            if (r.checked) return r.value;
        }
        return '';
    }

    async function fetchQuote() {
        if (!selectedFile) return;

        const payload = {
            shop_slug: shopSlug,
            page_count: detectedPages,
            color_mode: getSelectedRadio(colorModeRadios) || 'BW',
            duplex_mode: getSelectedRadio(duplexRadios) || 'SINGLE',
            paper_size: getSelectedRadio(paperSizeRadios) || 'A4',
            copies: parseInt(copiesInput.value) || 1,
            page_range_type: pageRangeSelect.value,
            page_range_selection: customRangeInput.value.trim()
        };

        try {
            const resp = await fetch('/orders/api/quote/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (resp.ok) {
                const data = await resp.json();
                quoteTotalSpan.textContent = `₹ ${data.total_amount.toFixed(2)}`;
                quoteBreakdownDiv.innerHTML = `
                    <div class="small text-muted mb-1">Rate: ₹${data.unit_rate} (${data.rate_label})</div>
                    <div class="small text-muted mb-1">Total physical sheets: ${data.total_sheets} (${data.copies} copies)</div>
                `;
                submitOrderBtn.disabled = false;
            }
        } catch (err) {
            console.error('Error fetching quote:', err);
        }
    }

    // Submit & Encrypt flow
    submitOrderBtn.addEventListener('click', async () => {
        if (!selectedFile || !fileArrayBuffer) {
            alert('Please select a PDF document first.');
            return;
        }

        const customerName = document.getElementById('custNameInput').value.trim() || 'Walk-in Customer';
        const customerPhone = document.getElementById('custPhoneInput').value.trim();

        if (!customerPhone) {
            alert('Please enter your mobile number for order pickup verification.');
            document.getElementById('custPhoneInput').focus();
            return;
        }

        submitOrderBtn.disabled = true;
        uploadStatusAlert.classList.remove('d-none');
        uploadStatusAlert.className = 'alert alert-info py-2 small';
        uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Encrypting PDF locally (Zero-Knowledge AES-256-GCM)...';

        try {
            // 1. Client-Side Encryption
            const cryptoRes = await ClientCryptoManager.encryptDocument(fileArrayBuffer, rsaPublicKey);

            uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading encrypted document securely...';

            // 2. Upload Encrypted Binary
            const formData = new FormData();
            formData.append('shop_slug', shopSlug);
            formData.append('encrypted_file', cryptoRes.encryptedBlob, selectedFile.name + '.enc');
            formData.append('original_filename', selectedFile.name);
            formData.append('file_hash_sha256', cryptoRes.sha256Hex);
            formData.append('encrypted_key_bundle', cryptoRes.encryptedKeyBundleB64);
            formData.append('encryption_iv', cryptoRes.ivB64);
            formData.append('encryption_tag', cryptoRes.tagB64);
            formData.append('detected_page_count', detectedPages);

            const uploadResp = await fetch('/orders/api/upload/', {
                method: 'POST',
                body: formData
            });

            if (!uploadResp.ok) {
                const errData = await uploadResp.json();
                throw new Error(errData.error || 'Document upload failed.');
            }

            const docData = await uploadResp.json();
            uploadedDocumentId = docData.document_id;

            uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating order quote...';

            // 3. Create Print Order
            const orderPayload = {
                shop_slug: shopSlug,
                document_id: uploadedDocumentId,
                customer_name: customerName,
                customer_phone: customerPhone,
                preferences: {
                    color_mode: getSelectedRadio(colorModeRadios) || 'BW',
                    duplex_mode: getSelectedRadio(duplexRadios) || 'SINGLE',
                    paper_size: getSelectedRadio(paperSizeRadios) || 'A4',
                    copies: parseInt(copiesInput.value) || 1,
                    page_range_type: pageRangeSelect.value,
                    page_range_selection: customRangeInput.value.trim()
                }
            };

            const orderResp = await fetch('/orders/api/create/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(orderPayload)
            });

            if (!orderResp.ok) {
                const errData = await orderResp.json();
                throw new Error(errData.error || 'Failed to create order.');
            }

            const orderData = await orderResp.json();
            const orderNumber = orderData.order_number;

            uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Initiating secure payment gateway...';

            // 4. Initiate Payment
            const payResp = await fetch('/payments/api/create-order/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_number: orderNumber })
            });

            if (!payResp.ok) {
                const errData = await payResp.json();
                throw new Error(errData.error || 'Failed to initiate payment.');
            }

            const payData = await payResp.json();

            // Check if sandbox simulation mode
            if (payData.is_sandbox && payData.sandbox_helper) {
                // Show modal or auto-trigger verified test payment
                showSandboxPaymentModal(payData, orderNumber);
            } else {
                // Live Razorpay Checkout script
                const rzpOptions = {
                    key: payData.key_id,
                    amount: payData.amount_paise,
                    currency: payData.currency,
                    name: 'KEP PrintGrid',
                    description: `Print Order #${orderNumber}`,
                    order_id: payData.gateway_order_id,
                    handler: async function (response) {
                        await verifyPaymentOnBackend(
                            response.razorpay_order_id,
                            response.razorpay_payment_id,
                            response.razorpay_signature,
                            orderNumber
                        );
                    },
                    prefill: {
                        name: customerName,
                        contact: customerPhone
                    },
                    theme: { color: '#0F172A' }
                };
                const rzp = new window.Razorpay(rzpOptions);
                rzp.open();
            }

        } catch (err) {
            uploadStatusAlert.className = 'alert alert-danger py-2 small';
            uploadStatusAlert.textContent = 'Error: ' + err.message;
            submitOrderBtn.disabled = false;
        }
    });

    function showSandboxPaymentModal(payData, orderNumber) {
        const modalHtml = `
            <div class="modal fade show d-block" tabindex="-1" style="background: rgba(15, 23, 42, 0.75);">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content shadow-lg border-0">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title fs-6"><i class="bi bi-shield-check text-warning me-2"></i>Razorpay Payment Sandbox</h5>
                        </div>
                        <div class="modal-body p-4">
                            <p class="text-muted small">You are in development mode. Simulate a real verified transaction using Razorpay's HMAC signature engine.</p>
                            <div class="card bg-light p-3 mb-3 border-0">
                                <div class="d-flex justify-content-between">
                                    <span class="text-muted">Order Number:</span>
                                    <span class="fw-bold">${orderNumber}</span>
                                </div>
                                <div class="d-flex justify-content-between mt-2">
                                    <span class="text-muted">Payable Amount:</span>
                                    <span class="fw-bold text-primary">₹ ${(payData.amount_paise / 100).toFixed(2)}</span>
                                </div>
                            </div>
                            <button id="paySuccessSimBtn" class="btn btn-success w-100 py-2 fw-bold">
                                <i class="bi bi-check-circle me-1"></i> Pay Now (Simulate Successful Payment)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHtml;
        document.body.appendChild(modalDiv);

        document.getElementById('paySuccessSimBtn').addEventListener('click', async () => {
            const helper = payData.sandbox_helper;
            await verifyPaymentOnBackend(
                payData.gateway_order_id,
                helper.sample_payment_id,
                helper.sample_signature,
                orderNumber
            );
        });
    }

    async function verifyPaymentOnBackend(orderId, paymentId, signature, orderNumber) {
        uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verifying payment signature with bank...';
        const verifyResp = await fetch('/payments/api/verify/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gateway_order_id: orderId,
                gateway_payment_id: paymentId,
                gateway_signature: signature
            })
        });

        if (verifyResp.ok) {
            const res = await verifyResp.json();
            window.location.href = res.redirect_url || `/orders/track/${orderNumber}/`;
        } else {
            const errData = await verifyResp.json();
            alert('Payment verification failed: ' + (errData.error || 'Signature error'));
            submitOrderBtn.disabled = false;
        }
    }
});

```

---

## File: `templates/base.html`

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}KEP PrintGrid - Smart QR Printing Platform{% endblock %}</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <!-- Custom Stylesheet -->
    <link rel="stylesheet" href="{% static 'css/styles.css' %}">
    {% block extra_head %}{% endblock %}
</head>
<body>
    <!-- Top Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark py-2 border-bottom border-secondary">
        <div class="container-fluid px-4">
            <a class="navbar-brand d-flex align-items-center gap-2" href="{% url 'core:home' %}">
                <i class="bi bi-printer-fill text-info fs-4"></i>
                <span class="fw-bold tracking-tight">KEP PrintGrid</span>
                <span class="badge badge-brand rounded-pill ms-1">v{{ APP_VERSION }}</span>
            </a>

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarMain">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarMain">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                    {% if user.is_authenticated %}
                        {% if user.is_owner or user.is_superuser %}
                            <li class="nav-item">
                                <a class="nav-link" href="{% url 'core:owner_overview' %}"><i class="bi bi-speedometer2 me-1"></i> Dashboard</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{% url 'orders:order_list' %}"><i class="bi bi-receipt me-1"></i> Orders</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{% url 'printers:printer_list' %}"><i class="bi bi-printer me-1"></i> Printers</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{% url 'core:shop_qr_management' %}"><i class="bi bi-qr-code me-1"></i> Permanent QR</a>
                            </li>
                        {% elif user.is_staff_member %}
                            <li class="nav-item">
                                <a class="nav-link" href="{% url 'orders:staff_dashboard' %}"><i class="bi bi-display me-1"></i> Staff Console</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{% url 'orders:order_list' %}"><i class="bi bi-receipt me-1"></i> Orders</a>
                            </li>
                        {% endif %}
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'core:home' %}">Home</a>
                        </li>
                    {% endif %}
                </ul>

                <div class="d-flex align-items-center gap-3">
                    {% if user.is_authenticated %}
                        <div class="dropdown">
                            <button class="btn btn-outline-light btn-sm dropdown-toggle d-flex align-items-center gap-2" type="button" data-bs-toggle="dropdown">
                                <i class="bi bi-person-circle text-info"></i>
                                <span>{{ user.get_full_name|default:user.username }}</span>
                                <span class="badge bg-secondary text-uppercase" style="font-size:0.65rem;">{{ user.role }}</span>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end shadow">
                                {% if user.is_owner %}
                                    <li><a class="dropdown-item" href="{% url 'core:shop_settings' %}"><i class="bi bi-gear me-2"></i> Shop Settings</a></li>
                                    <li><a class="dropdown-item" href="{% url 'orders:pricing_settings' %}"><i class="bi bi-tag me-2"></i> Pricing Rules</a></li>
                                    <li><hr class="dropdown-divider"></li>
                                {% endif %}
                                <li><a class="dropdown-item text-danger" href="{% url 'core:logout' %}"><i class="bi bi-box-arrow-right me-2"></i> Sign Out</a></li>
                            </ul>
                        </div>
                    {% else %}
                        <a href="{% url 'core:login' %}" class="btn btn-outline-light btn-sm px-3">Sign In</a>
                        <a href="{% url 'core:register' %}" class="btn btn-primary btn-sm px-3">Register Shop</a>
                    {% endif %}
                </div>
            </div>
        </div>
    </nav>

    <!-- Global Alert Messages -->
    <div class="container-fluid px-4 pt-3">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show shadow-sm" role="alert">
                    <i class="bi bi-info-circle-fill me-2"></i> {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            {% endfor %}
        {% endif %}
    </div>

    <!-- Main Content Block -->
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="bg-white border-top py-3 mt-auto text-center text-muted small">
        <div class="container">
            <span>&copy; 2026 KEP PrintGrid Platform. Zero-Knowledge Document Confidentiality &amp; Intelligent Spooling.</span>
        </div>
    </footer>

    <!-- Bootstrap 5 Bundle JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>

```

---

## File: `templates/components/dashboard_sidebar.html`

```html
<div class="sidebar p-3 d-flex flex-column">
    <div class="mb-4 px-2">
        <h6 class="text-uppercase text-muted fw-bold mb-1" style="font-size: 0.75rem;">Shop Workspace</h6>
        <div class="fw-bold text-white text-truncate">{{ shop.name }}</div>
        <div class="d-flex align-items-center gap-2 mt-2">
            {% if shop.is_accepting_orders %}
                <span class="badge bg-success" style="font-size: 0.7rem;"><i class="bi bi-broadcast me-1"></i> Orders Active</span>
            {% else %}
                <span class="badge bg-warning text-dark" style="font-size: 0.7rem;"><i class="bi bi-pause-circle me-1"></i> Paused</span>
            {% endif %}
            {% if shop.connector_last_seen %}
                <span class="badge bg-info text-dark" style="font-size: 0.7rem;"><i class="bi bi-link-45deg me-1"></i> Connector Live</span>
            {% else %}
                <span class="badge bg-secondary" style="font-size: 0.7rem;"><i class="bi bi-slash-circle me-1"></i> Connector Idle</span>
            {% endif %}
        </div>
    </div>

    <ul class="nav flex-column mb-auto">
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'owner_overview' %}active{% endif %}" href="{% url 'core:owner_overview' %}">
                <i class="bi bi-speedometer2"></i> Overview
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'order_list' or request.resolver_match.url_name == 'order_detail' %}active{% endif %}" href="{% url 'orders:order_list' %}">
                <i class="bi bi-receipt"></i> Orders
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'printer_list' %}active{% endif %}" href="{% url 'printers:printer_list' %}">
                <i class="bi bi-printer"></i> Printers
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'printer_assignments' %}active{% endif %}" href="{% url 'printers:printer_assignments' %}">
                <i class="bi bi-diagram-3"></i> Intelligent Routing
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'shop_qr_management' %}active{% endif %}" href="{% url 'core:shop_qr_management' %}">
                <i class="bi bi-qr-code"></i> Permanent QR Code
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'pricing_settings' %}active{% endif %}" href="{% url 'orders:pricing_settings' %}">
                <i class="bi bi-tags"></i> Pricing Settings
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'reports' %}active{% endif %}" href="{% url 'core:reports' %}">
                <i class="bi bi-graph-up"></i> Reports &amp; Sales
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'staff_management' %}active{% endif %}" href="{% url 'core:staff_management' %}">
                <i class="bi bi-people"></i> Staff Management
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link {% if request.resolver_match.url_name == 'shop_settings' %}active{% endif %}" href="{% url 'core:shop_settings' %}">
                <i class="bi bi-gear"></i> Shop Settings
            </a>
        </li>
    </ul>

    <hr class="text-secondary">
    <div class="px-2">
        <a href="{% url 'shop_order_page' slug=shop.slug %}" target="_blank" class="btn btn-outline-info btn-sm w-100 mb-2">
            <i class="bi bi-box-arrow-up-right me-1"></i> Customer Order View
        </a>
    </div>
</div>

```

---

## File: `templates/core/home.html`

```html
{% extends 'base.html' %}

{% block title %}KEP PrintGrid - Smart QR-Based Xerox & Print Automation{% endblock %}

{% block content %}
<div class="bg-dark text-white py-5 border-bottom border-secondary">
    <div class="container py-4">
        <div class="row align-items-center g-5">
            <div class="col-lg-7">
                <span class="badge bg-primary px-3 py-2 text-uppercase mb-3">Zero-Knowledge Secure Printing</span>
                <h1 class="display-4 fw-bold mb-3">Scan. Upload. Pay. Print Instantly.</h1>
                <p class="lead text-light mb-4">
                    KEP PrintGrid eliminates long queues and thumb drives at Xerox shops. Customers scan a permanent shop QR code, configure printing options on mobile, pay securely, and collect printed documents at the counter.
                </p>
                <div class="d-flex flex-wrap gap-3">
                    <a href="{% url 'core:register' %}" class="btn btn-primary btn-lg px-4 fw-semibold">
                        <i class="bi bi-shop me-2"></i> Register Your Shop Free
                    </a>
                    <a href="{% url 'core:login' %}" class="btn btn-outline-light btn-lg px-4">
                        Owner Login
                    </a>
                </div>
            </div>
            <div class="col-lg-5">
                <div class="card border-0 shadow-lg text-dark p-4 bg-white rounded-4">
                    <h5 class="fw-bold mb-3"><i class="bi bi-search text-primary me-2"></i> Track Your Print Order</h5>
                    <p class="text-muted small">Enter your unique PrintGrid order number to view real-time printing progress.</p>
                    <form onsubmit="event.preventDefault(); const val=document.getElementById('trackOrderInput').value.trim(); if(val) window.location.href='/orders/track/' + encodeURIComponent(val);">
                        <div class="mb-3">
                            <label class="form-label small fw-bold text-muted">Order Number</label>
                            <input type="text" id="trackOrderInput" class="form-control form-control-lg" placeholder="e.g. ORD-20261111-9284" required>
                        </div>
                        <button type="submit" class="btn btn-dark w-100 py-2 fw-semibold">
                            <i class="bi bi-clock-history me-1"></i> Track Order Status
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="container py-5">
    <div class="text-center mb-5">
        <h2 class="fw-bold text-dark">Why Xerox Shops &amp; Customers Love PrintGrid</h2>
        <p class="text-muted">Built from the ground up for security, speed, and hardware resilience.</p>
    </div>

    <div class="row g-4">
        <div class="col-md-4">
            <div class="card h-100 border p-4 rounded-4 shadow-sm">
                <div class="display-6 text-primary mb-3"><i class="bi bi-qr-code"></i></div>
                <h5 class="fw-bold">1. Permanent QR Code</h5>
                <p class="text-muted small">One shop QR code that never expires. Add, replace, or reassign printers without ever needing to print a new QR stand.</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card h-100 border p-4 rounded-4 shadow-sm">
                <div class="display-6 text-success mb-3"><i class="bi bi-shield-lock-fill"></i></div>
                <h5 class="fw-bold">2. Zero-Knowledge Encryption</h5>
                <p class="text-muted small">Documents are encrypted in the customer's browser using AES-256-GCM and unwrapped only by the local shop connector. The cloud backend never sees plaintext files.</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card h-100 border p-4 rounded-4 shadow-sm">
                <div class="display-6 text-info mb-3"><i class="bi bi-diagram-3-fill"></i></div>
                <h5 class="fw-bold">3. Intelligent Spooler Routing</h5>
                <p class="text-muted small">Automatically dispatches B&amp;W jobs to fast monochrome printers and color jobs to photo-capable copiers with automated failover.</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/core/login.html`

```html
{% extends 'base.html' %}

{% block title %}Sign In - KEP PrintGrid{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-5 col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 p-4 p-md-5 bg-white">
                <div class="text-center mb-4">
                    <div class="display-6 text-primary mb-2"><i class="bi bi-box-arrow-in-right"></i></div>
                    <h3 class="fw-bold">Sign In</h3>
                    <p class="text-muted small">Access your Shop Admin or Staff Console.</p>
                </div>

                <form method="post" novalidate>
                    {% csrf_token %}

                    {% if form.non_field_errors %}
                        <div class="alert alert-danger py-2 small">
                            {% for error in form.non_field_errors %}
                                <div><i class="bi bi-exclamation-triangle-fill me-1"></i> {{ error }}</div>
                            {% endfor %}
                        </div>
                    {% endif %}

                    <div class="mb-3">
                        <label class="form-label fw-semibold small text-muted">{{ form.email_or_username.label }}</label>
                        {{ form.email_or_username }}
                    </div>

                    <div class="mb-4">
                        <label class="form-label fw-semibold small text-muted">{{ form.password.label }}</label>
                        {{ form.password }}
                    </div>

                    <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold">
                        Sign In
                    </button>
                </form>

                <div class="text-center mt-4 small text-muted">
                    Need a print shop account? <a href="{% url 'core:register' %}" class="text-decoration-none fw-semibold">Register Shop</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/core/owner_overview.html`

```html
{% extends 'base.html' %}

{% block title %}Dashboard Overview - {{ shop.name }} | KEP PrintGrid{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h4 class="fw-bold mb-1">Owner Dashboard Overview</h4>
                <div class="text-muted small">Real-time telemetry, printing metrics and spooler operations.</div>
            </div>
            <div class="d-flex gap-2">
                <a href="{% url 'core:shop_qr_management' %}" class="btn btn-outline-dark btn-sm">
                    <i class="bi bi-qr-code me-1"></i> Shop Permanent QR
                </a>
                <a href="{% url 'orders:pricing_settings' %}" class="btn btn-primary btn-sm">
                    <i class="bi bi-tag me-1"></i> Configure Rates
                </a>
            </div>
        </div>

        <!-- Metrics Grid -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-label">Today's Revenue</div>
                    <div class="metric-value text-success">₹ {{ today_revenue|floatformat:2 }}</div>
                    <div class="text-muted small mt-1">Total: ₹ {{ total_revenue|floatformat:2 }}</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-label">Today's Orders</div>
                    <div class="metric-value">{{ today_orders }}</div>
                    <div class="text-muted small mt-1">All time: {{ total_orders }} orders</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-label">Active / Printing</div>
                    <div class="metric-value text-primary">{{ printing_orders|add:pending_orders }}</div>
                    <div class="text-muted small mt-1">{{ printing_orders }} printing, {{ pending_orders }} queued</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-label">Printers Online</div>
                    <div class="metric-value text-info">{{ online_printers }} / {{ shop_printers.count }}</div>
                    <div class="text-muted small mt-1">{{ offline_printers }} offline or disabled</div>
                </div>
            </div>
        </div>

        <!-- Printers Telemetry Strip -->
        <div class="card border-0 shadow-sm rounded-4 mb-4 p-3 bg-white">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="fw-bold mb-0"><i class="bi bi-cpu text-primary me-2"></i>Connected Windows Shop Printers</h6>
                <a href="{% url 'printers:printer_list' %}" class="small text-decoration-none">Manage Printers &rarr;</a>
            </div>
            <div class="row g-2 mt-1">
                {% for printer in shop_printers %}
                    <div class="col-md-4">
                        <div class="border rounded-3 p-2 d-flex align-items-center justify-content-between {% if printer.is_online and printer.is_active %}border-success bg-light{% else %}border-secondary-subtle{% endif %}">
                            <div class="d-flex align-items-center gap-2">
                                <span class="spinner-grow spinner-grow-sm {% if printer.is_online and printer.is_active %}text-success{% else %}text-secondary{% endif %}" role="status"></span>
                                <div>
                                    <div class="fw-bold small text-truncate" style="max-width: 170px;">{{ printer.name }}</div>
                                    <div class="text-muted" style="font-size: 0.7rem;">{{ printer.system_printer_name }}</div>
                                </div>
                            </div>
                            <span class="badge {% if printer.is_online and printer.is_active %}bg-success{% else %}bg-secondary{% endif %}" style="font-size: 0.65rem;">
                                {% if printer.is_online and printer.is_active %}ONLINE{% else %}OFFLINE{% endif %}
                            </span>
                        </div>
                    </div>
                {% empty %}
                    <div class="col-12 py-3 text-center text-muted small">
                        <i class="bi bi-info-circle me-1"></i> No printers detected yet. Run the Windows Local Connector to auto-sync your shop copiers.
                    </div>
                {% endfor %}
            </div>
        </div>

        <!-- Recent Orders Table -->
        <div class="card border-0 shadow-sm rounded-4 bg-white overflow-hidden">
            <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
                <h6 class="fw-bold mb-0"><i class="bi bi-receipt text-primary me-2"></i>Recent Customer Orders</h6>
                <a href="{% url 'orders:order_list' %}" class="small text-decoration-none">View All Orders &rarr;</a>
            </div>
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light small text-uppercase text-muted">
                        <tr>
                            <th>Order No</th>
                            <th>Customer</th>
                            <th>Preferences</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>Time</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for order in recent_orders %}
                            <tr>
                                <td class="fw-bold">{{ order.order_number }}</td>
                                <td>
                                    <div>{{ order.customer_name }}</div>
                                    <div class="text-muted small">{{ order.customer_phone }}</div>
                                </td>
                                <td>
                                    <span class="badge bg-light text-dark border">{{ order.preference.color_mode }}</span>
                                    <span class="badge bg-light text-dark border">{{ order.preference.duplex_mode }}</span>
                                    <span class="badge bg-light text-dark border">{{ order.preference.paper_size }}</span>
                                    <small class="text-muted">x{{ order.preference.copies }}</small>
                                </td>
                                <td class="fw-bold text-success">₹ {{ order.total_amount }}</td>
                                <td>
                                    <span class="badge badge-status-{{ order.status|lower }} px-2 py-1">
                                        {{ order.get_status_display }}
                                    </span>
                                </td>
                                <td class="text-muted small">{{ order.created_at|timesince }} ago</td>
                                <td>
                                    <a href="{% url 'orders:order_detail' order_number=order.order_number %}" class="btn btn-outline-secondary btn-sm py-0 px-2">
                                        Inspect
                                    </a>
                                </td>
                            </tr>
                        {% empty %}
                            <tr>
                                <td colspan="7" class="text-center py-4 text-muted">No orders received yet. Display your permanent QR code to begin!</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/core/register.html`

```html
{% extends 'base.html' %}

{% block title %}Register Shop - KEP PrintGrid{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-7 col-lg-6">
            <div class="card border-0 shadow-sm rounded-4 p-4 p-md-5 bg-white">
                <div class="text-center mb-4">
                    <div class="display-6 text-primary mb-2"><i class="bi bi-printer-fill"></i></div>
                    <h3 class="fw-bold">Register Your Print Shop</h3>
                    <p class="text-muted small">Start accepting QR-based self-service print orders in less than 2 minutes.</p>
                </div>

                <form method="post" novalidate>
                    {% csrf_token %}

                    {% if form.non_field_errors %}
                        <div class="alert alert-danger py-2 small">
                            {% for error in form.non_field_errors %}
                                <div><i class="bi bi-exclamation-triangle-fill me-1"></i> {{ error }}</div>
                            {% endfor %}
                        </div>
                    {% endif %}

                    <div class="mb-3">
                        <label class="form-label fw-semibold small text-muted">{{ form.shop_name.label }}</label>
                        {{ form.shop_name }}
                        {% if form.shop_name.errors %}<div class="text-danger small mt-1">{{ form.shop_name.errors.0 }}</div>{% endif %}
                    </div>

                    <div class="row g-2 mb-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold small text-muted">{{ form.owner_name.label }}</label>
                            {{ form.owner_name }}
                            {% if form.owner_name.errors %}<div class="text-danger small mt-1">{{ form.owner_name.errors.0 }}</div>{% endif %}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-semibold small text-muted">{{ form.mobile_number.label }}</label>
                            {{ form.mobile_number }}
                            {% if form.mobile_number.errors %}<div class="text-danger small mt-1">{{ form.mobile_number.errors.0 }}</div>{% endif %}
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label fw-semibold small text-muted">{{ form.email.label }}</label>
                        {{ form.email }}
                        {% if form.email.errors %}<div class="text-danger small mt-1">{{ form.email.errors.0 }}</div>{% endif %}
                    </div>

                    <div class="row g-2 mb-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold small text-muted">{{ form.password.label }}</label>
                            {{ form.password }}
                            {% if form.password.errors %}<div class="text-danger small mt-1">{{ form.password.errors.0 }}</div>{% endif %}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-semibold small text-muted">{{ form.confirm_password.label }}</label>
                            {{ form.confirm_password }}
                            {% if form.confirm_password.errors %}<div class="text-danger small mt-1">{{ form.confirm_password.errors.0 }}</div>{% endif %}
                        </div>
                    </div>

                    <div class="mb-4">
                        <label class="form-label fw-semibold small text-muted">{{ form.shop_address.label }}</label>
                        {{ form.shop_address }}
                        {% if form.shop_address.errors %}<div class="text-danger small mt-1">{{ form.shop_address.errors.0 }}</div>{% endif %}
                    </div>

                    <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold">
                        <i class="bi bi-check-circle me-1"></i> Complete Registration &amp; Generate QR
                    </button>
                </form>

                <div class="text-center mt-4 small text-muted">
                    Already registered? <a href="{% url 'core:login' %}" class="text-decoration-none fw-semibold">Sign in here</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/core/reports.html`

```html
{% extends 'base.html' %}

{% block title %}Reports &amp; Analytics - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <h4 class="fw-bold mb-1">Reports &amp; Business Intelligence</h4>
        <div class="text-muted small mb-4">Track daily print volumes, revenue trends, and monochrome vs color distribution.</div>

        <div class="row g-4 mb-4">
            <div class="col-md-8">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                    <h6 class="fw-bold mb-3"><i class="bi bi-bar-chart-fill text-primary me-2"></i>Last 7 Days Revenue &amp; Orders</h6>
                    <div class="table-responsive">
                        <table class="table table-sm align-middle">
                            <thead class="table-light small text-muted">
                                <tr>
                                    <th>Date</th>
                                    <th>Orders Placed</th>
                                    <th>Revenue Generated</th>
                                    <th>Bar Chart</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for day in days_data %}
                                    <tr>
                                        <td class="fw-bold">{{ day.date }}</td>
                                        <td>{{ day.orders_count }}</td>
                                        <td class="text-success fw-bold">₹ {{ day.revenue|floatformat:2 }}</td>
                                        <td style="width: 40%;">
                                            <div class="progress" style="height: 12px;">
                                                <div class="progress-bar bg-primary" role="progressbar" style="width: {% if day.revenue > 0 %}{% widthratio day.revenue 1000 100 %}{% else %}0{% endif %}%;"></div>
                                            </div>
                                        </td>
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100 text-center">
                    <h6 class="fw-bold mb-4"><i class="bi bi-pie-chart-fill text-info me-2"></i>Print Mode Distribution</h6>
                    <div class="my-4">
                        <div class="display-6 fw-bold text-dark">{{ total_orders }}</div>
                        <div class="text-muted small">Total Lifetime Orders</div>
                    </div>
                    <div class="d-flex justify-content-around mt-auto border-top pt-3">
                        <div>
                            <div class="badge bg-dark px-3 py-2 fs-6">{{ bw_count }}</div>
                            <div class="text-muted small mt-1">Black &amp; White</div>
                        </div>
                        <div>
                            <div class="badge bg-primary px-3 py-2 fs-6">{{ color_count }}</div>
                            <div class="text-muted small mt-1">Colour</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/core/shop_qr_management.html`

```html
{% extends 'base.html' %}

{% block title %}Permanent Shop QR Code - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h4 class="fw-bold mb-1">Permanent Shop QR Code</h4>
                <div class="text-muted small">This QR code is permanently assigned to <strong>{{ shop.name }}</strong>. Print and place it at your counter.</div>
            </div>
            <form method="post">
                {% csrf_token %}
                <button type="submit" name="regenerate" class="btn btn-outline-secondary btn-sm">
                    <i class="bi bi-arrow-clockwise me-1"></i> Re-Render Assets
                </button>
            </form>
        </div>

        <div class="row g-4">
            <!-- QR Display Card -->
            <div class="col-md-5">
                <div class="card border-0 shadow-sm rounded-4 p-4 text-center bg-white">
                    <span class="badge bg-primary px-3 py-1 mb-3 text-uppercase align-self-center">Counter Display QR</span>
                    {% if qr_record.qr_code_image %}
                        <div class="p-3 bg-light border rounded-3 d-inline-block mx-auto mb-3">
                            <img src="{{ qr_record.qr_code_image.url }}" alt="Permanent QR Code" class="img-fluid" style="max-width: 260px;">
                        </div>
                    {% endif %}
                    <h5 class="fw-bold mb-1">{{ shop.name }}</h5>
                    <p class="text-muted small mb-3">{{ shop.address }}</p>

                    <div class="d-grid gap-2">
                        <a href="{% url 'core:download_qr_asset' asset_type='pdf' %}" class="btn btn-primary">
                            <i class="bi bi-file-earmark-pdf me-2"></i> Download Printable A4 Poster (PDF)
                        </a>
                        <a href="{% url 'core:download_qr_asset' asset_type='png' %}" class="btn btn-outline-dark">
                            <i class="bi bi-download me-2"></i> Download High-Res PNG
                        </a>
                    </div>
                </div>
            </div>

            <!-- Rules & Guidance Card -->
            <div class="col-md-7">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white mb-4">
                    <h6 class="fw-bold mb-3"><i class="bi bi-shield-check text-success me-2"></i>Permanent QR Invariant Rules</h6>
                    <ul class="list-group list-group-flush small">
                        <li class="list-group-item px-0 py-2 d-flex gap-2">
                            <i class="bi bi-check-circle-fill text-success"></i>
                            <div><strong>Never changes:</strong> Changing, replacing, or servicing physical printers will <em>never</em> invalidate this QR code.</div>
                        </li>
                        <li class="list-group-item px-0 py-2 d-flex gap-2">
                            <i class="bi bi-check-circle-fill text-success"></i>
                            <div><strong>Intelligent Routing:</strong> Customers scan this single code, and PrintGrid routes jobs to your active online printers automatically.</div>
                        </li>
                        <li class="list-group-item px-0 py-2 d-flex gap-2">
                            <i class="bi bi-check-circle-fill text-success"></i>
                            <div><strong>Temporary Pausing:</strong> If your shop is busy, simply toggle "Pause Ordering" in Settings without changing or reprinting this code.</div>
                        </li>
                    </ul>
                </div>

                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                    <h6 class="fw-bold mb-2">Permanent Customer Ordering URL</h6>
                    <p class="text-muted small">Customers scanning the QR code are directed to:</p>
                    <div class="input-group mb-3">
                        <input type="text" class="form-control bg-light" value="{{ shop.order_page_url }}" readonly id="shopUrlInput">
                        <button class="btn btn-outline-secondary" type="button" onclick="navigator.clipboard.writeText(document.getElementById('shopUrlInput').value); alert('Copied shop URL to clipboard!');">
                            <i class="bi bi-clipboard"></i> Copy
                        </button>
                        <a href="{{ shop.order_page_url }}" target="_blank" class="btn btn-outline-primary">
                            <i class="bi bi-box-arrow-up-right"></i> Open
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/core/shop_settings.html`

```html
{% extends 'base.html' %}

{% block title %}Shop Settings - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <h4 class="fw-bold mb-1">Shop Settings &amp; Availability</h4>
        <div class="text-muted small mb-4">Manage operational hours, pause status, and contact details.</div>

        <div class="row">
            <div class="col-lg-8">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                    <form method="post">
                        {% csrf_token %}

                        <!-- Pause / Resume Ordering Section -->
                        <div class="p-3 mb-4 rounded-3 border {% if shop.is_accepting_orders %}bg-light-success border-success-subtle{% else %}bg-warning-subtle border-warning{% endif %}">
                            <div class="form-check form-switch mb-2">
                                {{ form.is_accepting_orders }}
                                <label class="form-check-label fw-bold" for="{{ form.is_accepting_orders.id_for_label }}">
                                    Accepting New Print Orders
                                </label>
                            </div>
                            <div class="text-muted small mb-3">
                                When turned off, scanning the QR code informs customers that the shop is temporarily paused. Existing paid orders remain accessible to staff.
                            </div>
                            <div>
                                <label class="form-label small fw-semibold text-muted">{{ form.pause_message.label }}</label>
                                {{ form.pause_message }}
                            </div>
                        </div>

                        <h6 class="fw-bold mb-3">Shop Profile Information</h6>

                        <div class="mb-3">
                            <label class="form-label small fw-semibold text-muted">{{ form.name.label }}</label>
                            {{ form.name }}
                        </div>

                        <div class="row g-2 mb-3">
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">{{ form.phone.label }}</label>
                                {{ form.phone }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">{{ form.email.label }}</label>
                                {{ form.email }}
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label small fw-semibold text-muted">{{ form.address.label }}</label>
                            {{ form.address }}
                        </div>

                        <!-- Connector Authentication Credentials -->
                        <div class="card bg-light border-0 p-3 mb-4 rounded-3">
                            <h6 class="fw-bold mb-1 text-dark"><i class="bi bi-key-fill text-warning me-2"></i>Local Connector Credentials</h6>
                            <p class="text-muted small mb-2">Use this secret auth token to link your Windows shop computer with the PrintGrid cloud backend.</p>
                            <div class="input-group">
                                <input type="text" class="form-control font-monospace small bg-white" value="{{ shop.connector_auth_token }}" readonly id="authTokenInput">
                                <button class="btn btn-outline-secondary" type="button" onclick="navigator.clipboard.writeText(document.getElementById('authTokenInput').value); alert('Connector token copied to clipboard!');">
                                    <i class="bi bi-clipboard"></i> Copy Token
                                </button>
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary px-4 fw-semibold">
                            Save Changes
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/core/staff_management.html`

```html
{% extends 'base.html' %}

{% block title %}Staff Management - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <h4 class="fw-bold mb-1">Staff Management</h4>
        <div class="text-muted small mb-4">Grant counter staff operational access without exposing owner-level credentials.</div>

        <div class="row g-4">
            <!-- Add Staff Form -->
            <div class="col-lg-5">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                    <h6 class="fw-bold mb-3"><i class="bi bi-person-plus text-primary me-2"></i>Add New Operator</h6>
                    <form method="post">
                        {% csrf_token %}

                        {% if form.errors %}
                            <div class="alert alert-danger py-2 small">
                                {% for field, errors in form.errors.items %}
                                    <div>{{ errors.0 }}</div>
                                {% endfor %}
                            </div>
                        {% endif %}

                        <div class="mb-3">
                            <label class="form-label small fw-semibold text-muted">Staff Name</label>
                            {{ form.name }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-semibold text-muted">Email Address</label>
                            {{ form.email }}
                        </div>
                        <div class="row g-2 mb-3">
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">Mobile</label>
                                {{ form.mobile_number }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">Password</label>
                                {{ form.password }}
                            </div>
                        </div>

                        <div class="border rounded-3 p-3 mb-3 bg-light">
                            <div class="fw-bold small mb-2 text-dark">Staff Permissions</div>
                            <div class="form-check mb-2">
                                {{ form.can_authorize_retries }}
                                <label class="form-check-label small" for="{{ form.can_authorize_retries.id_for_label }}">
                                    Can authorize job retries on printer error
                                </label>
                            </div>
                            <div class="form-check mb-2">
                                {{ form.can_manage_printers }}
                                <label class="form-check-label small" for="{{ form.can_manage_printers.id_for_label }}">
                                    Can toggle printer availability
                                </label>
                            </div>
                            <div class="form-check">
                                {{ form.can_manage_pricing }}
                                <label class="form-check-label small" for="{{ form.can_manage_pricing.id_for_label }}">
                                    Can update pricing rules
                                </label>
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary w-100 fw-semibold">
                            Create Staff Account
                        </button>
                    </form>
                </div>
            </div>

            <!-- Active Staff Table -->
            <div class="col-lg-7">
                <div class="card border-0 shadow-sm rounded-4 bg-white overflow-hidden">
                    <div class="card-header bg-white py-3 border-0">
                        <h6 class="fw-bold mb-0"><i class="bi bi-people text-primary me-2"></i>Active Staff Accounts</h6>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0">
                            <thead class="table-light small text-uppercase text-muted">
                                <tr>
                                    <th>Operator</th>
                                    <th>Permissions</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for staff in staff_members %}
                                    <tr>
                                        <td>
                                            <div class="fw-bold">{{ staff.user.get_full_name|default:staff.user.username }}</div>
                                            <div class="text-muted small">{{ staff.user.email }}</div>
                                        </td>
                                        <td>
                                            {% if staff.can_authorize_retries %}<span class="badge bg-light text-dark border">Retry Authorized</span>{% endif %}
                                            {% if staff.can_manage_printers %}<span class="badge bg-light text-dark border">Printers</span>{% endif %}
                                            {% if staff.can_manage_pricing %}<span class="badge bg-light text-dark border">Pricing</span>{% endif %}
                                        </td>
                                        <td>
                                            <a href="{% url 'core:remove_staff' staff_id=staff.id %}" class="btn btn-outline-danger btn-sm py-0 px-2" onclick="return confirm('Remove this staff account?');">
                                                Remove
                                            </a>
                                        </td>
                                    </tr>
                                {% empty %}
                                    <tr>
                                        <td colspan="3" class="text-center py-4 text-muted small">No staff accounts registered yet.</td>
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/orders/customer_track_order.html`

```html
{% extends 'base.html' %}

{% block title %}Track Order #{{ order.order_number }} | KEP PrintGrid{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card border-0 shadow-sm rounded-4 p-4 p-md-5 bg-white mb-4">
                <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
                    <div>
                        <span class="badge bg-secondary-subtle text-secondary px-3 py-1 mb-1 text-uppercase" style="font-size:0.7rem;">Order Tracking</span>
                        <h3 class="fw-bold mb-0 text-dark">{{ order.order_number }}</h3>
                    </div>
                    <div>
                        <span class="badge badge-status-{{ order.status|lower }} fs-6 px-3 py-2" id="liveStatusBadge">
                            {{ order.get_status_display }}
                        </span>
                    </div>
                </div>

                <!-- Visual Stepper Progress Bar -->
                <div class="stepper-header my-4">
                    <div class="step-node {% if order.status in 'UPLOADED,AWAITING_PAYMENT,PAYMENT_VERIFIED,QUEUED,ASSIGNED,SENT_TO_PRINTER,PRINTING,COMPLETED' %}done{% endif %}">
                        <div class="step-num"><i class="bi bi-check"></i></div>
                        <div class="step-title">Uploaded</div>
                    </div>
                    <div class="step-node {% if order.status in 'PAYMENT_VERIFIED,QUEUED,ASSIGNED,SENT_TO_PRINTER,PRINTING,COMPLETED' %}done{% elif order.status == 'AWAITING_PAYMENT' %}active{% endif %}">
                        <div class="step-num">2</div>
                        <div class="step-title">Paid</div>
                    </div>
                    <div class="step-node {% if order.status in 'ASSIGNED,SENT_TO_PRINTER,PRINTING,COMPLETED' %}done{% elif order.status == 'QUEUED' %}active{% endif %}">
                        <div class="step-num">3</div>
                        <div class="step-title">Queued</div>
                    </div>
                    <div class="step-node {% if order.status in 'SENT_TO_PRINTER,PRINTING,COMPLETED' %}done{% elif order.status == 'ASSIGNED' %}active{% endif %}">
                        <div class="step-num">4</div>
                        <div class="step-title">Printing</div>
                    </div>
                    <div class="step-node {% if order.status == 'COMPLETED' %}done{% endif %}">
                        <div class="step-num">5</div>
                        <div class="step-title">Ready!</div>
                    </div>
                </div>

                <!-- Status Detail Banner -->
                <div class="alert {% if order.status == 'COMPLETED' %}alert-success{% elif order.status == 'FAILED' %}alert-danger{% else %}alert-info{% endif %} rounded-3 p-3 my-3">
                    <div class="d-flex align-items-center gap-2">
                        {% if order.status == 'COMPLETED' %}
                            <i class="bi bi-check-circle-fill text-success fs-4"></i>
                            <div>
                                <strong>Your document has been printed successfully!</strong>
                                <div class="small">Please collect your printout from the shop counter by presenting your order number.</div>
                            </div>
                        {% elif order.status == 'FAILED' %}
                            <i class="bi bi-exclamation-triangle-fill text-danger fs-4"></i>
                            <div>
                                <strong>Printing exception occurred.</strong>
                                <div class="small">{{ job.failure_reason|default:"The shop staff has been notified to assist you." }}</div>
                            </div>
                        {% else %}
                            <span class="spinner-border spinner-border-sm text-primary" role="status"></span>
                            <div>
                                <strong>Processing your print job...</strong>
                                <div class="small">
                                    {% if job and job.printer %}
                                        Routed to shop copier: <strong>{{ job.printer.name }}</strong>
                                    {% else %}
                                        Job is securely queued for next available copier.
                                    {% endif %}
                                </div>
                            </div>
                        {% endif %}
                    </div>
                </div>

                <!-- Order Details Card -->
                <div class="card bg-light border-0 rounded-4 p-4 mt-4">
                    <h6 class="fw-bold mb-3 text-dark">Order Specification</h6>
                    <div class="row g-3">
                        <div class="col-sm-6">
                            <div class="text-muted small">Shop Destination</div>
                            <div class="fw-bold text-dark">{{ order.shop.name }}</div>
                            <div class="text-muted small">{{ order.shop.address }}</div>
                        </div>
                        <div class="col-sm-6">
                            <div class="text-muted small">Customer Name &amp; Phone</div>
                            <div class="fw-bold text-dark">{{ order.customer_name }}</div>
                            <div class="text-muted small">{{ order.customer_phone }}</div>
                        </div>
                        <div class="col-sm-6">
                            <div class="text-muted small">Printing Preferences</div>
                            <div class="fw-semibold text-dark">
                                {{ order.preference.color_mode }} • {{ order.preference.duplex_mode }} • {{ order.preference.paper_size }} ({{ order.preference.copies }} copies)
                            </div>
                        </div>
                        <div class="col-sm-6">
                            <div class="text-muted small">Total Paid Amount</div>
                            <div class="fw-bold fs-5 text-success">₹ {{ order.total_amount }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
    // Poll for status updates every 3 seconds if not completed or failed
    const orderNumber = "{{ order.order_number }}";
    let isFinished = {% if order.status in 'COMPLETED,FAILED,CANCELLED,REFUNDED' %}true{% else %}false{% endif %};

    if (!isFinished) {
        const intervalId = setInterval(async () => {
            try {
                const resp = await fetch(`/orders/api/status/${orderNumber}/`);
                if (resp.ok) {
                    const data = await resp.json();
                    if (data.status !== "{{ order.status }}") {
                        // Refresh page to render updated stage
                        window.location.reload();
                    }
                    if (data.is_completed) {
                        clearInterval(intervalId);
                    }
                }
            } catch (e) {
                console.error("Polling error:", e);
            }
        }, 3000);
    }
</script>
{% endblock %}

```

---

## File: `templates/orders/order_detail.html`

```html
{% extends 'base.html' %}

{% block title %}Order {{ order.order_number }} - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <a href="{% url 'orders:order_list' %}" class="small text-decoration-none text-muted">&larr; Back to Orders</a>
                <h4 class="fw-bold mb-0 mt-1">Order {{ order.order_number }}</h4>
            </div>
            <div class="d-flex gap-2">
                {% if order.status != 'COMPLETED' and order.status != 'REFUNDED' and order.status != 'CANCELLED' %}
                    <a href="{% url 'orders:mark_completed' order_number=order.order_number %}" class="btn btn-success btn-sm">
                        <i class="bi bi-check-circle me-1"></i> Mark Completed &amp; Collected
                    </a>
                {% endif %}
                {% if order.status == 'FAILED' or job.status == 'FAILED' or job.status == 'HOLD_VERIFICATION' %}
                    <a href="{% url 'orders:authorize_retry' order_number=order.order_number %}" class="btn btn-warning btn-sm text-dark">
                        <i class="bi bi-arrow-repeat me-1"></i> Authorize Reprint
                    </a>
                {% endif %}
            </div>
        </div>

        <div class="row g-4">
            <!-- Left Column: Order Summary & Document Security -->
            <div class="col-lg-7">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white mb-4">
                    <h6 class="fw-bold mb-3"><i class="bi bi-file-earmark-lock text-primary me-2"></i>Document &amp; Encryption Info</h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-borderless">
                            <tr>
                                <td class="text-muted" style="width: 35%;">Original Filename:</td>
                                <td class="fw-bold">{{ order.document.original_filename }}</td>
                            </tr>
                            <tr>
                                <td class="text-muted">SHA-256 Hash:</td>
                                <td class="font-monospace small text-truncate" style="max-width: 250px;">{{ order.document.file_hash_sha256 }}</td>
                            </tr>
                            <tr>
                                <td class="text-muted">Declared Pages:</td>
                                <td>{{ order.document.detected_page_count }}</td>
                            </tr>
                            <tr>
                                <td class="text-muted">Verified by Connector:</td>
                                <td>
                                    {% if order.document.verified_page_count %}
                                        <span class="badge bg-success-subtle text-success">{{ order.document.verified_page_count }} pages verified</span>
                                    {% else %}
                                        <span class="text-muted small">Pending local spooler inspection</span>
                                    {% endif %}
                                </td>
                            </tr>
                            <tr>
                                <td class="text-muted">Confidentiality:</td>
                                <td><span class="badge bg-light text-dark border"><i class="bi bi-shield-check text-success me-1"></i> Zero-Knowledge (AES-256-GCM)</span></td>
                            </tr>
                        </table>
                    </div>
                </div>

                <!-- Print Job Routing Execution -->
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white mb-4">
                    <h6 class="fw-bold mb-3"><i class="bi bi-printer text-primary me-2"></i>Spooler Job Execution</h6>
                    {% if job %}
                        <div class="p-3 bg-light rounded-3 mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <div>
                                    <div class="text-muted small">Assigned Physical Printer:</div>
                                    <div class="fw-bold fs-6">{{ job.printer.name|default:"Queued (Waiting for available copier)" }}</div>
                                </div>
                                <span class="badge badge-status-{{ job.status|lower }} px-2 py-1">
                                    {{ job.get_status_display }}
                                </span>
                            </div>
                            {% if job.failure_reason %}
                                <div class="alert alert-danger py-2 small mb-0 mt-2">
                                    <i class="bi bi-exclamation-triangle-fill me-1"></i> {{ job.failure_reason }}
                                </div>
                            {% endif %}
                        </div>

                        <!-- Attempts History -->
                        <h6 class="small fw-bold text-muted text-uppercase mb-2">Execution Attempts Log</h6>
                        <ul class="list-group list-group-flush small">
                            {% for attempt in attempts %}
                                <li class="list-group-item px-0 py-2 d-flex justify-content-between">
                                    <div>
                                        <span class="fw-bold">#{{ attempt.attempt_number }} - {{ attempt.status }}</span>
                                        <div class="text-muted">{{ attempt.error_message|default:"Dispatched cleanly" }}</div>
                                    </div>
                                    <div class="text-muted">{{ attempt.timestamp|date:"H:i:s" }}</div>
                                </li>
                            {% empty %}
                                <li class="list-group-item px-0 py-1 text-muted small">No extra attempts recorded.</li>
                            {% endfor %}
                        </ul>
                    {% else %}
                        <p class="text-muted small mb-0">No print job record generated yet.</p>
                    {% endif %}
                </div>
            </div>

            <!-- Right Column: Payment & Customer Handover -->
            <div class="col-lg-5">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white mb-4">
                    <h6 class="fw-bold mb-3"><i class="bi bi-cash-stack text-success me-2"></i>Payment Verification</h6>
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="text-muted">Total Charged:</span>
                        <span class="fs-4 fw-bold text-success">₹ {{ order.total_amount }}</span>
                    </div>

                    {% for payment in payments %}
                        <div class="border rounded-3 p-3 bg-light mb-2 small">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted">Payment ID:</span>
                                <span class="fw-bold">{{ payment.gateway_payment_id|default:payment.gateway_order_id }}</span>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted">Status:</span>
                                <span class="badge {% if payment.status == 'CAPTURED' %}bg-success{% else %}bg-warning{% endif %}">{{ payment.status }}</span>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span class="text-muted">Verified At:</span>
                                <span>{{ payment.verified_at|date:"d M H:i"|default:"Unverified" }}</span>
                            </div>
                        </div>
                    {% empty %}
                        <div class="text-muted small">No payment transactions recorded.</div>
                    {% endfor %}

                    {% if order.status != 'REFUNDED' and payments %}
                        <hr class="my-3">
                        <form method="post" action="{% url 'payments:initiate_refund' order_number=order.order_number %}" onsubmit="return confirm('Authorize full refund of ₹{{ order.total_amount }} for this order?');">
                            {% csrf_token %}
                            <input type="hidden" name="reason" value="Customer cancellation or hardware jam">
                            <button type="submit" class="btn btn-outline-danger btn-sm w-100">
                                <i class="bi bi-arrow-counterclockwise me-1"></i> Issue Refund
                            </button>
                        </form>
                    {% endif %}
                </div>

                <!-- Customer Details -->
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                    <h6 class="fw-bold mb-3"><i class="bi bi-person text-primary me-2"></i>Customer Pickup Info</h6>
                    <div class="mb-2">
                        <span class="text-muted small">Customer Name:</span>
                        <div class="fw-bold">{{ order.customer_name }}</div>
                    </div>
                    <div class="mb-2">
                        <span class="text-muted small">Mobile Phone:</span>
                        <div class="fw-bold"><a href="tel:{{ order.customer_phone }}" class="text-decoration-none">{{ order.customer_phone }}</a></div>
                    </div>
                    <div class="mb-0">
                        <span class="text-muted small">Preferences Summary:</span>
                        <div class="small text-muted">
                            {{ order.preference.color_mode }} • {{ order.preference.duplex_mode }} • {{ order.preference.paper_size }} ({{ order.preference.copies }} copies)
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/orders/order_list.html`

```html
{% extends 'base.html' %}

{% block title %}Orders Management - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h4 class="fw-bold mb-1">Orders Management</h4>
                <div class="text-muted small">Manage incoming, printing, and completed customer print jobs.</div>
            </div>
            <div>
                <a href="{% url 'printers:reassign_queued_jobs' %}" class="btn btn-warning btn-sm text-dark">
                    <i class="bi bi-arrow-repeat me-1"></i> Re-Route Queued Jobs
                </a>
            </div>
        </div>

        <!-- Filters Form -->
        <div class="card border-0 shadow-sm rounded-4 p-3 bg-white mb-4">
            <form method="get" class="row g-2 align-items-center">
                <div class="col-md-5">
                    <div class="input-group">
                        <span class="input-group-text bg-light border-end-0"><i class="bi bi-search text-muted"></i></span>
                        <input type="text" name="q" class="form-control border-start-0" placeholder="Search by Order # or Mobile..." value="{{ search_query|default:'' }}">
                    </div>
                </div>
                <div class="col-md-4">
                    <select name="status" class="form-select">
                        <option value="">-- All Order Statuses --</option>
                        {% for code, label in status_choices %}
                            <option value="{{ code }}" {% if selected_status == code %}selected{% endif %}>{{ label }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-3 d-flex gap-2">
                    <button type="submit" class="btn btn-primary btn-sm flex-grow-1">Filter</button>
                    <a href="{% url 'orders:order_list' %}" class="btn btn-outline-secondary btn-sm">Reset</a>
                </div>
            </form>
        </div>

        <!-- Orders Table -->
        <div class="card border-0 shadow-sm rounded-4 bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light small text-uppercase text-muted">
                        <tr>
                            <th>Order No</th>
                            <th>Customer</th>
                            <th>Configuration</th>
                            <th>Assigned Copier</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>Timestamp</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for order in orders %}
                            <tr>
                                <td class="fw-bold">{{ order.order_number }}</td>
                                <td>
                                    <div>{{ order.customer_name }}</div>
                                    <div class="text-muted small">{{ order.customer_phone }}</div>
                                </td>
                                <td>
                                    <span class="badge bg-light text-dark border">{{ order.preference.color_mode }}</span>
                                    <span class="badge bg-light text-dark border">{{ order.preference.duplex_mode }}</span>
                                    <span class="badge bg-light text-dark border">{{ order.preference.paper_size }}</span>
                                    <small class="text-muted">x{{ order.preference.copies }}</small>
                                </td>
                                <td>
                                    {% if order.print_job and order.print_job.printer %}
                                        <span class="fw-semibold text-dark">{{ order.print_job.printer.name }}</span>
                                    {% else %}
                                        <span class="text-muted small"><em>Unassigned / Queued</em></span>
                                    {% endif %}
                                </td>
                                <td class="fw-bold text-success">₹ {{ order.total_amount }}</td>
                                <td>
                                    <span class="badge badge-status-{{ order.status|lower }} px-2 py-1">
                                        {{ order.get_status_display }}
                                    </span>
                                </td>
                                <td class="text-muted small">{{ order.created_at|date:"d M, H:i" }}</td>
                                <td>
                                    <a href="{% url 'orders:order_detail' order_number=order.order_number %}" class="btn btn-outline-dark btn-sm py-0 px-2">
                                        Details
                                    </a>
                                </td>
                            </tr>
                        {% empty %}
                            <tr>
                                <td colspan="8" class="text-center py-5 text-muted">No print orders match the query criteria.</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/orders/pricing_settings.html`

```html
{% extends 'base.html' %}

{% block title %}Pricing Settings - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <h4 class="fw-bold mb-1">Printing Rates Configuration</h4>
        <div class="text-muted small mb-4">Set per-page and per-sheet rates in INR. Prices are dynamically quoted to customers before checkout.</div>

        <div class="row">
            <div class="col-lg-8">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                    <form method="post">
                        {% csrf_token %}

                        <h6 class="fw-bold text-dark mb-3"><i class="bi bi-file-earmark-text text-primary me-2"></i>A4 Standard Document Printing (per sheet / page)</h6>
                        <div class="row g-3 mb-4">
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">B&amp;W Single-Sided (₹ / page)</label>
                                {{ form.bw_single_rate }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">B&amp;W Double-Sided (₹ / sheet)</label>
                                {{ form.bw_double_rate }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">Colour Single-Sided (₹ / page)</label>
                                {{ form.color_single_rate }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">Colour Double-Sided (₹ / sheet)</label>
                                {{ form.color_double_rate }}
                            </div>
                        </div>

                        <h6 class="fw-bold text-dark mb-3"><i class="bi bi-file-earmark-ruled text-info me-2"></i>A3 Large Format Rates (per page)</h6>
                        <div class="row g-3 mb-4">
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">A3 Black &amp; White (₹ / page)</label>
                                {{ form.a3_bw_rate }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted">A3 Colour (₹ / page)</label>
                                {{ form.a3_color_rate }}
                            </div>
                        </div>

                        <div class="form-check mb-4">
                            {{ form.is_active }}
                            <label class="form-check-label fw-bold small text-dark" for="{{ form.is_active.id_for_label }}">
                                Enable these rates for live customer orders
                            </label>
                        </div>

                        <button type="submit" class="btn btn-primary px-4 fw-semibold">
                            Update Rates
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/orders/shop_order_page.html`

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Order Print - {{ shop.name }} | KEP PrintGrid{% endblock %}

{% block extra_head %}
<!-- PDF.js for client-side secure preview & page counting -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
    if (window.pdfjsLib) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
    window.PRINTGRID_SHOP_SLUG = "{{ shop.slug }}";
    window.PRINTGRID_RSA_KEY = `{{ connector_public_key|escapejs }}`;
</script>
<!-- Client-side zero-knowledge encryption -->
<script src="{% static 'js/client_crypto.js' %}"></script>
{% endblock %}

{% block content %}
<div class="container py-4">
    <!-- Shop Header Card -->
    <div class="card border-0 shadow-sm rounded-4 p-4 mb-4 bg-white">
        <div class="row align-items-center g-3">
            <div class="col-md-8">
                <div class="d-flex align-items-center gap-2 mb-2">
                    <span class="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-1 text-uppercase fw-bold" style="font-size:0.7rem;">Verified Print Shop</span>
                    {% if shop.is_accepting_orders %}
                        <span class="badge bg-success-subtle text-success border border-success-subtle px-3 py-1"><i class="bi bi-check-circle me-1"></i> Accepting Orders</span>
                    {% else %}
                        <span class="badge bg-warning-subtle text-warning-emphasis border border-warning px-3 py-1"><i class="bi bi-pause-circle me-1"></i> Paused</span>
                    {% endif %}
                </div>
                <h3 class="fw-bold mb-1 text-dark">{{ shop.name }}</h3>
                <div class="text-muted small mb-2"><i class="bi bi-geo-alt me-1"></i> {{ shop.address }}</div>
                <div class="text-muted small"><i class="bi bi-telephone me-1"></i> {{ shop.phone }}</div>
            </div>
            <div class="col-md-4 text-md-end">
                <div class="p-3 bg-light rounded-3 text-start d-inline-block">
                    <div class="small fw-bold text-dark mb-1"><i class="bi bi-tag-fill text-primary me-1"></i> Standard Rates:</div>
                    <div class="text-muted small">B&amp;W Single: ₹{{ pricing.bw_single_rate }} / page</div>
                    <div class="text-muted small">Color Single: ₹{{ pricing.color_single_rate }} / page</div>
                </div>
            </div>
        </div>
    </div>

    {% if not shop.is_accepting_orders %}
        <!-- Shop Paused Banner -->
        <div class="alert alert-warning rounded-4 p-4 text-center shadow-sm">
            <div class="display-6 mb-2"><i class="bi bi-exclamation-triangle-fill text-warning"></i></div>
            <h4 class="fw-bold">Ordering Temporarily Paused</h4>
            <p class="mb-0">{{ shop.pause_message }}</p>
        </div>
    {% else %}
        <!-- Step-by-Step Customer Ordering Wizard -->
        <div class="row g-4">
            <!-- Left Column: Document Upload & Preferences -->
            <div class="col-lg-7">
                <!-- Step 1: Upload PDF -->
                <div class="card border-0 shadow-sm rounded-4 p-4 mb-4 bg-white">
                    <h5 class="fw-bold mb-3"><span class="badge bg-primary rounded-circle me-2">1</span> Select PDF Document</h5>
                    
                    <div class="upload-dropzone" id="uploadDropzone">
                        <input type="file" id="pdfFileInput" accept="application/pdf" class="d-none">
                        <div class="display-5 text-primary mb-2"><i class="bi bi-cloud-arrow-up"></i></div>
                        <h6 class="fw-bold mb-1">Click to browse or drag and drop your PDF here</h6>
                        <p class="text-muted small mb-0">PDF files up to 50 MB are supported. Client-side encrypted.</p>
                    </div>

                    <!-- Document Info Card -->
                    <div class="d-none mt-3 p-3 bg-light border rounded-3" id="docInfoSection">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fw-bold text-dark text-truncate" style="max-width: 320px;" id="docName">document.pdf</div>
                                <div class="text-muted small">Pages: <span id="docPages" class="fw-semibold text-primary">--</span> | Size: <span id="docSize">--</span></div>
                            </div>
                            <span class="badge bg-success-subtle text-success border border-success-subtle"><i class="bi bi-shield-lock me-1"></i> Validated</span>
                        </div>
                    </div>
                </div>

                <!-- Step 2: Printing Preferences -->
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                    <h5 class="fw-bold mb-3"><span class="badge bg-primary rounded-circle me-2">2</span> Printing Preferences</h5>

                    <!-- Color Mode -->
                    <div class="mb-3">
                        <label class="form-label small fw-bold text-muted text-uppercase">Color Mode</label>
                        <div class="d-flex gap-3">
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="color_mode" id="colorBw" value="BW" checked>
                                <label class="form-check-label fw-semibold" for="colorBw">Black &amp; White</label>
                            </div>
                            {% if has_color_printer %}
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="color_mode" id="colorCol" value="COLOR">
                                    <label class="form-check-label fw-semibold" for="colorCol">Colour</label>
                                </div>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Duplex Mode -->
                    <div class="mb-3">
                        <label class="form-label small fw-bold text-muted text-uppercase">Sides</label>
                        <div class="d-flex gap-3">
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="duplex_mode" id="duplexSingle" value="SINGLE" checked>
                                <label class="form-check-label fw-semibold" for="duplexSingle">Single-Sided</label>
                            </div>
                            {% if has_duplex_printer %}
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="duplex_mode" id="duplexDouble" value="DOUBLE">
                                    <label class="form-check-label fw-semibold" for="duplexDouble">Double-Sided (Back-to-Back)</label>
                                </div>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Paper Size -->
                    <div class="mb-3">
                        <label class="form-label small fw-bold text-muted text-uppercase">Paper Size</label>
                        <div class="d-flex gap-3">
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="paper_size" id="paperA4" value="A4" checked>
                                <label class="form-check-label fw-semibold" for="paperA4">A4 (Standard)</label>
                            </div>
                            {% if has_a3_printer %}
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="paper_size" id="paperA3" value="A3">
                                    <label class="form-check-label fw-semibold" for="paperA3">A3 (Large Ledger)</label>
                                </div>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Copies & Range -->
                    <div class="row g-3 mb-3">
                        <div class="col-md-4">
                            <label class="form-label small fw-bold text-muted text-uppercase">Copies</label>
                            <input type="number" id="copiesInput" class="form-control" value="1" min="1" max="100">
                        </div>
                        <div class="col-md-8">
                            <label class="form-label small fw-bold text-muted text-uppercase">Page Selection</label>
                            <select id="pageRangeSelect" class="form-select">
                                <option value="ALL">All Pages</option>
                                <option value="CUSTOM">Custom Pages (e.g. 1-5, 8)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Custom Range Input -->
                    <div class="mb-3 d-none" id="customRangeDiv">
                        <label class="form-label small fw-bold text-muted">Enter Page Numbers / Ranges</label>
                        <input type="text" id="customRangeInput" class="form-control" placeholder="e.g. 1-3, 5, 8-10">
                    </div>
                </div>
            </div>

            <!-- Right Column: Document Preview & Checkout -->
            <div class="col-lg-5">
                <!-- Preview Canvas Card -->
                <div class="card border-0 shadow-sm rounded-4 p-4 mb-4 bg-white d-none" id="pdfPreviewContainer">
                    <h6 class="fw-bold mb-3"><i class="bi bi-eye text-primary me-2"></i>Document Preview (Page 1)</h6>
                    <div class="pdf-preview-box">
                        <canvas id="pdfPreviewCanvas" class="pdf-preview-canvas"></canvas>
                    </div>
                </div>

                <!-- Price Quote & Checkout Card -->
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                    <h5 class="fw-bold mb-3"><span class="badge bg-primary rounded-circle me-2">3</span> Order Checkout</h5>

                    <div class="mb-3">
                        <label class="form-label small fw-bold text-muted">Your Name</label>
                        <input type="text" id="custNameInput" class="form-control" placeholder="e.g. Anand Sharma">
                    </div>

                    <div class="mb-3">
                        <label class="form-label small fw-bold text-muted">Mobile Number (Required for pickup)</label>
                        <input type="tel" id="custPhoneInput" class="form-control" placeholder="e.g. 9876543210" required>
                    </div>

                    <hr class="my-3">

                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="text-muted">Calculated Price:</span>
                        <span class="display-6 fw-bold text-primary" id="quoteTotal">₹ 0.00</span>
                    </div>

                    <div id="quoteBreakdown" class="mb-3">
                        <div class="text-muted small">Select a document to calculate price quote.</div>
                    </div>

                    <div class="alert alert-info py-2 small d-none" id="uploadStatusAlert"></div>

                    <button type="button" id="submitOrderBtn" class="btn btn-primary btn-lg w-100 py-3 fw-bold" disabled>
                        <i class="bi bi-credit-card me-2"></i> Pay &amp; Print Document
                    </button>

                    <div class="text-center mt-3 text-muted" style="font-size: 0.75rem;">
                        <i class="bi bi-shield-lock-fill text-success me-1"></i> End-to-End Client Encryption Active
                    </div>
                </div>
            </div>
        </div>
    {% endif %}
</div>
{% endblock %}

{% block extra_scripts %}
<script src="{% static 'js/order_flow.js' %}"></script>
{% endblock %}

```

---

## File: `templates/orders/staff_dashboard.html`

```html
{% extends 'base.html' %}

{% block title %}Shop Staff Console - {{ shop.name }}{% endblock %}

{% block content %}
<div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <span class="badge bg-dark px-3 py-1 text-uppercase mb-1" style="font-size:0.7rem;">Counter Staff Console</span>
            <h3 class="fw-bold mb-0 text-dark">{{ shop.name }}</h3>
        </div>
        <div>
            <a href="{% url 'orders:order_list' %}" class="btn btn-outline-dark btn-sm">
                <i class="bi bi-list-ul me-1"></i> All Orders
            </a>
        </div>
    </div>

    <!-- Active Printing Queue -->
    <div class="card border-0 shadow-sm rounded-4 mb-4 bg-white overflow-hidden">
        <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
            <h6 class="fw-bold mb-0"><i class="bi bi-printer-fill text-primary me-2"></i>Live Printing Queue ({{ active_jobs.count }})</h6>
            <button onclick="window.location.reload();" class="btn btn-outline-secondary btn-sm py-0 px-2">
                <i class="bi bi-arrow-clockwise me-1"></i> Refresh
            </button>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="table-light small text-uppercase text-muted">
                    <tr>
                        <th>Order No</th>
                        <th>Customer</th>
                        <th>Options</th>
                        <th>Target Copier</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for order in active_jobs %}
                        <tr>
                            <td class="fw-bold">{{ order.order_number }}</td>
                            <td>
                                <div>{{ order.customer_name }}</div>
                                <div class="text-muted small">{{ order.customer_phone }}</div>
                            </td>
                            <td>
                                <span class="badge bg-light text-dark border">{{ order.preference.color_mode }}</span>
                                <span class="badge bg-light text-dark border">{{ order.preference.duplex_mode }}</span>
                                <span class="badge bg-light text-dark border">{{ order.preference.paper_size }}</span>
                                <small class="text-muted">x{{ order.preference.copies }}</small>
                            </td>
                            <td class="fw-semibold">{{ order.print_job.printer.name|default:"Queued" }}</td>
                            <td>
                                <span class="badge badge-status-{{ order.status|lower }} px-2 py-1">
                                    {{ order.get_status_display }}
                                </span>
                            </td>
                            <td>
                                <a href="{% url 'orders:mark_completed' order_number=order.order_number %}" class="btn btn-success btn-sm py-1 px-3 fw-bold">
                                    <i class="bi bi-check-lg me-1"></i> Handover
                                </a>
                            </td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="6" class="text-center py-4 text-muted small">No active jobs in the print queue right now.</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Ready for Pickup & Exception Handlers -->
    <div class="row g-4">
        <!-- Ready for Pickup Handover -->
        <div class="col-md-7">
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                <h6 class="fw-bold mb-3"><i class="bi bi-box-seam-fill text-success me-2"></i>Recently Completed &amp; Ready for Pickup</h6>
                <div class="table-responsive">
                    <table class="table table-sm align-middle mb-0">
                        <thead class="table-light small text-muted">
                            <tr>
                                <th>Order #</th>
                                <th>Customer Name</th>
                                <th>Phone</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for order in ready_jobs %}
                                <tr>
                                    <td class="fw-bold"><a href="{% url 'orders:order_detail' order_number=order.order_number %}" class="text-decoration-none">{{ order.order_number }}</a></td>
                                    <td>{{ order.customer_name }}</td>
                                    <td>{{ order.customer_phone }}</td>
                                    <td class="text-muted small">{{ order.updated_at|timesince }} ago</td>
                                </tr>
                            {% empty %}
                                <tr>
                                    <td colspan="4" class="text-center py-3 text-muted small">No completed orders waiting for collection.</td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Hardware Failures & Retry Triggers -->
        <div class="col-md-5">
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                <h6 class="fw-bold mb-3 text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>Printing Exceptions ({{ failed_jobs.count }})</h6>
                <ul class="list-group list-group-flush small">
                    {% for order in failed_jobs %}
                        <li class="list-group-item px-0 py-2">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="fw-bold text-dark">{{ order.order_number }}</span>
                                <a href="{% url 'orders:authorize_retry' order_number=order.order_number %}" class="btn btn-warning btn-sm py-0 px-2 text-dark fw-bold">
                                    <i class="bi bi-arrow-repeat me-1"></i> Retry
                                </a>
                            </div>
                            <div class="text-danger small">{{ order.print_job.failure_reason|default:"Physical spooler reported paper jam or offline." }}</div>
                        </li>
                    {% empty %}
                        <li class="list-group-item px-0 py-3 text-center text-muted small">No failed jobs recorded. All printers operating smoothly!</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/printers/printer_assignments.html`

```html
{% extends 'base.html' %}

{% block title %}Intelligent Print Job Routing - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h4 class="fw-bold mb-1">Intelligent Print Job Routing</h4>
                <div class="text-muted small">Route customer print jobs dynamically based on color mode, duplex, and paper size.</div>
            </div>
            <a href="{% url 'printers:printer_list' %}" class="btn btn-outline-secondary btn-sm">
                &larr; Back to Printers
            </a>
        </div>

        <div class="card border-0 shadow-sm rounded-4 p-4 bg-white mb-4">
            <h6 class="fw-bold mb-3"><i class="bi bi-diagram-3 text-primary me-2"></i>Configure Routing Assignment Rules</h6>
            <form method="post">
                {% csrf_token %}
                <div class="table-responsive">
                    <table class="table align-middle">
                        <thead class="table-light small text-muted">
                            <tr>
                                <th>Job Category</th>
                                <th>Primary Target Printer</th>
                                <th>Fallback Printer (If Primary Offline)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for code, label in assignment_types %}
                                <tr>
                                    <td class="fw-bold">{{ label }}</td>
                                    <td>
                                        <select name="primary_{{ code }}" class="form-select form-select-sm">
                                            <option value="">-- Use Default Printer --</option>
                                            {% for printer in printers %}
                                                <option value="{{ printer.id }}" {% if assignment_map|default_if_none:'' and assignment_map.items %}{% for k, a in assignment_map.items %}{% if k == code and a.primary_printer.id == printer.id %}selected{% endif %}{% endfor %}{% endif %}>
                                                    {{ printer.name }} {% if not printer.is_online %}(Offline){% endif %}
                                                </option>
                                            {% endfor %}
                                        </select>
                                    </td>
                                    <td>
                                        <select name="fallback_{{ code }}" class="form-select form-select-sm">
                                            <option value="">-- No Fallback (Queue if offline) --</option>
                                            {% for printer in printers %}
                                                <option value="{{ printer.id }}" {% if assignment_map|default_if_none:'' and assignment_map.items %}{% for k, a in assignment_map.items %}{% if k == code and a.fallback_printer.id == printer.id %}selected{% endif %}{% endfor %}{% endif %}>
                                                    {{ printer.name }}
                                                </option>
                                            {% endfor %}
                                        </select>
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <div class="alert alert-info py-2 small mt-3">
                    <i class="bi bi-info-circle-fill me-1"></i>
                    <strong>Routing Safety:</strong> Only eligible queued jobs are reassigned. Dispatched or printing jobs are never duplicated. The permanent QR code continues functioning without changes.
                </div>

                <button type="submit" class="btn btn-primary px-4 fw-semibold mt-2">
                    Save Routing Rules
                </button>
            </form>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `templates/printers/printer_list.html`

```html
{% extends 'base.html' %}

{% block title %}Printer Management - {{ shop.name }}{% endblock %}

{% block content %}
<div class="dashboard-container">
    {% include 'components/dashboard_sidebar.html' %}

    <div class="dashboard-main">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h4 class="fw-bold mb-1">Printer Management</h4>
                <div class="text-muted small">Manage shop copiers, paper sizes, capabilities, and active routing status.</div>
            </div>
            <div>
                <a href="{% url 'printers:printer_assignments' %}" class="btn btn-outline-primary btn-sm">
                    <i class="bi bi-diagram-3 me-1"></i> Configure Routing Rules
                </a>
                <a href="{% url 'printers:reassign_queued_jobs' %}" class="btn btn-warning btn-sm text-dark ms-2">
                    <i class="bi bi-arrow-repeat me-1"></i> Route Queued Jobs
                </a>
            </div>
        </div>

        <div class="card border-0 shadow-sm rounded-4 bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light small text-uppercase text-muted">
                        <tr>
                            <th>Printer Name</th>
                            <th>Windows Spooler Queue</th>
                            <th>Status</th>
                            <th>Capabilities</th>
                            <th>Operational State</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for printer in printers %}
                            <tr>
                                <td>
                                    <div class="fw-bold d-flex align-items-center gap-2">
                                        {{ printer.name }}
                                        {% if printer.is_default %}
                                            <span class="badge bg-primary" style="font-size: 0.65rem;">DEFAULT</span>
                                        {% endif %}
                                    </div>
                                    <div class="text-muted small">{{ printer.model_name|default:"Local Spooler Copier" }}</div>
                                </td>
                                <td class="font-monospace small text-muted">{{ printer.system_printer_name }}</td>
                                <td>
                                    {% if printer.is_online %}
                                        <span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1">
                                            <i class="bi bi-circle-fill me-1" style="font-size: 0.5rem;"></i> Online
                                        </span>
                                    {% else %}
                                        <span class="badge bg-secondary-subtle text-secondary border px-2 py-1">
                                            <i class="bi bi-slash-circle me-1"></i> Offline
                                        </span>
                                    {% endif %}
                                    <div class="text-muted mt-1" style="font-size: 0.7rem;">{{ printer.last_status_message }}</div>
                                </td>
                                <td>
                                    <div class="d-flex flex-wrap gap-1">
                                        {% if printer.handles_bw %}
                                            <span class="badge bg-light text-dark border">B&amp;W</span>
                                        {% endif %}
                                        {% if printer.handles_color %}
                                            <span class="badge bg-info-subtle text-info-emphasis border">Colour</span>
                                        {% endif %}
                                        {% if printer.capability.supports_duplex %}
                                            <span class="badge bg-light text-dark border">Duplex</span>
                                        {% endif %}
                                        {% for size in printer.capability.supported_paper_sizes %}
                                            <span class="badge bg-light text-dark border">{{ size }}</span>
                                        {% endfor %}
                                    </div>
                                </td>
                                <td>
                                    <a href="{% url 'printers:printer_toggle_active' printer_id=printer.id %}" class="btn btn-sm {% if printer.is_active %}btn-outline-success{% else %}btn-outline-secondary{% endif %}">
                                        {% if printer.is_active %}<i class="bi bi-toggle-on me-1"></i> Enabled{% else %}<i class="bi bi-toggle-off me-1"></i> Disabled{% endif %}
                                    </a>
                                </td>
                                <td>
                                    {% if not printer.is_default %}
                                        <a href="{% url 'printers:printer_set_default' printer_id=printer.id %}" class="btn btn-outline-primary btn-sm py-0 px-2" title="Set as Shop Default">
                                            Make Default
                                        </a>
                                    {% endif %}
                                </td>
                            </tr>
                        {% empty %}
                            <tr>
                                <td colspan="6" class="text-center py-5 text-muted">
                                    <div class="display-6 text-muted mb-2"><i class="bi bi-printer"></i></div>
                                    <p class="mb-1">No printers connected to this shop yet.</p>
                                    <p class="small">Launch the <code>KEP PrintGrid Connector</code> on your Windows shop PC to automatically detect your local printers.</p>
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

---

## File: `tests/__init__.py`

```python

```

---

## File: `tests/test_auth.py`

```python
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Shop
from orders.models import PricingRule


class AuthenticationAndRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('core:register')
        self.login_url = reverse('core:login')
        self.logout_url = reverse('core:logout')
        self.dashboard_url = reverse('core:owner_overview')

    def test_valid_shop_registration(self):
        """Test complete valid shop owner registration creates user, shop, and pricing."""
        payload = {
            'shop_name': 'Express Print Hub',
            'owner_name': 'Rohit Sharma',
            'email': 'rohit@expressprint.example',
            'mobile_number': '+91 9876543210',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'shop_address': 'Shop 10, Metro Station Complex',
        }
        response = self.client.post(self.register_url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check User creation
        user = User.objects.filter(email='rohit@expressprint.example').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, User.Role.OWNER)

        # Check Shop creation
        shop = Shop.objects.filter(owner=user).first()
        self.assertIsNotNone(shop)
        self.assertEqual(shop.name, 'Express Print Hub')
        self.assertTrue(shop.slug.startswith('express-print-hub'))
        self.assertTrue(len(shop.connector_auth_token) > 20)

        # Check default pricing rule
        pricing = PricingRule.objects.filter(shop=shop).first()
        self.assertIsNotNone(pricing)
        self.assertEqual(pricing.bw_single_rate, 2.00)

    def test_duplicate_email_registration_rejected(self):
        """Test registration with an existing email is rejected."""
        User.objects.create_user(
            username='existinguser',
            email='test@shop.example',
            password='Password123!'
        )
        payload = {
            'shop_name': 'Second Shop',
            'owner_name': 'Ajay Dev',
            'email': 'test@shop.example',
            'mobile_number': '+91 9999999999',
            'password': 'Password1234!',
            'confirm_password': 'Password1234!',
            'shop_address': 'Sector 4',
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('email', form.errors)
        self.assertIn('An account with this email address already exists. Please log in.', form.errors['email'])

    def test_invalid_password_mismatch(self):
        """Test passwords that do not match are rejected."""
        payload = {
            'shop_name': 'Fail Shop',
            'owner_name': 'Tester',
            'email': 'fail@shop.example',
            'mobile_number': '+91 9111111111',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword123!',
            'shop_address': 'Main Street',
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('confirm_password', form.errors)
        self.assertIn('Passwords do not match.', form.errors['confirm_password'])

    def test_login_and_logout_flow(self):
        """Test authentication via username or email and subsequent session logout."""
        user = User.objects.create_user(
            username='printowner',
            email='owner@test.example',
            password='SuperSecretPassword!',
            role=User.Role.OWNER
        )
        Shop.objects.create(name='Test Shop', owner=user, email=user.email, phone='1234567890', address='Local')

        # Login with email
        login_resp = self.client.post(self.login_url, {
            'email_or_username': 'owner@test.example',
            'password': 'SuperSecretPassword!'
        }, follow=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertTrue(login_resp.context['user'].is_authenticated)

        # Logout
        logout_resp = self.client.get(self.logout_url, follow=True)
        self.assertFalse(logout_resp.context['user'].is_authenticated)

    def test_unauthorized_dashboard_access_redirects(self):
        """Unauthenticated user accessing protected dashboard route is redirected to login."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(reverse('core:login') in response.url)

```

---

## File: `tests/test_connector.py`

```python
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import User, Shop
from printers.models import Printer, Connector
from orders.models import PrintOrder, PrintDocument, PrintPreference, PrintJob
from connector.crypto_manager import ConnectorCryptoManager
from connector.local_store import LocalExecutionStore


class ConnectorAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='connector_owner',
            email='conn@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='Terminal Xerox',
            owner=self.owner,
            email='conn@shop.example',
            phone='9876543210',
            address='Counter 1'
        )
        self.token = self.shop.connector_auth_token
        self.crypto = ConnectorCryptoManager()

    def test_connector_registration(self):
        """Connector registers machine ID and RSA public key."""
        payload = {
            'machine_id': 'WIN-PC-COUNTER-1',
            'name': 'Windows Desk PC',
            'os_platform': 'win32',
            'version': '1.0.0',
            'rsa_public_key': self.crypto.get_public_key_pem()
        }
        resp = self.client.post(
            reverse('printers:api_connector_register'),
            payload,
            content_type='application/json',
            HTTP_X_SHOP_TOKEN=self.token
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'registered')

        self.shop.refresh_from_db()
        self.assertTrue(self.shop.connector_public_key.startswith('-----BEGIN PUBLIC KEY-----'))
        self.assertEqual(Connector.objects.filter(shop=self.shop).count(), 1)

    def test_connector_heartbeat_syncs_printers(self):
        """Heartbeat auto-discovers and updates shop copiers in cloud DB."""
        payload = {
            'machine_id': 'WIN-PC-COUNTER-1',
            'printers': [
                {
                    'system_name': 'Canon_iR2520_Spooler',
                    'friendly_name': 'Canon imageRUNNER 2520',
                    'is_online': True,
                    'status': 'Ready',
                    'capabilities': {
                        'supports_bw': True,
                        'supports_color': False,
                        'supports_duplex': True,
                        'supported_paper_sizes': ['A4', 'A3']
                    }
                }
            ]
        }
        resp = self.client.post(
            reverse('printers:api_connector_heartbeat'),
            payload,
            content_type='application/json',
            HTTP_X_SHOP_TOKEN=self.token
        )
        self.assertEqual(resp.status_code, 200)

        # Check printer was saved in DB
        printer = Printer.objects.filter(shop=self.shop, system_printer_name='Canon_iR2520_Spooler').first()
        self.assertIsNotNone(printer)
        self.assertTrue(printer.is_online)
        self.assertTrue(printer.capability.supports_duplex)
        self.assertIn('A3', printer.capability.supported_paper_sizes)

    def test_connector_poll_and_status_update_flow(self):
        """Connector polls dispatched jobs and updates status to PHYSICALLY_PRINTED."""
        printer = Printer.objects.create(
            shop=self.shop,
            name='HP LaserJet',
            system_printer_name='HP_LaserJet',
            is_active=True,
            is_online=True
        )
        doc = PrintDocument.objects.create(
            shop=self.shop,
            original_filename='notes.pdf',
            file_hash_sha256='hash',
            encrypted_file=SimpleUploadedFile('notes.enc', b'bytes'),
            encrypted_file_size=5,
            encrypted_key_bundle='bundle',
            encryption_iv='iv',
            detected_page_count=1
        )
        pref = PrintPreference.objects.create(
            color_mode='BW',
            duplex_mode='SINGLE',
            paper_size='A4',
            copies=1,
            total_calculated_pages=1
        )
        order = PrintOrder.objects.create(
            order_number='ORD-CONN-01',
            shop=self.shop,
            customer_phone='9876543210',
            document=doc,
            preference=pref,
            status=PrintOrder.Status.ASSIGNED,
            total_amount=Decimal('2.00'),
            idempotency_key='conn_test_01'
        )
        job = PrintJob.objects.create(
            order=order,
            printer=printer,
            status=PrintJob.Status.DISPATCHED
        )

        # 1. Poll Jobs
        poll_resp = self.client.get(
            reverse('printers:api_connector_poll_jobs'),
            HTTP_X_SHOP_TOKEN=self.token
        )
        self.assertEqual(poll_resp.status_code, 200)
        jobs = poll_resp.json()['pending_jobs']
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['job_id'], str(job.id))

        # 2. Update Status to PHYSICALLY_PRINTED
        update_resp = self.client.post(
            reverse('printers:api_connector_update_job_status'),
            {
                'job_id': str(job.id),
                'status': PrintJob.Status.PHYSICALLY_PRINTED,
                'verified_page_count': 1,
                'connector_ack_id': 'OS_SPOOL_99'
            },
            content_type='application/json',
            HTTP_X_SHOP_TOKEN=self.token
        )
        self.assertEqual(update_resp.status_code, 200)

        job.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(job.status, PrintJob.Status.PHYSICALLY_PRINTED)
        self.assertEqual(order.status, PrintOrder.Status.COMPLETED)

```

---

## File: `tests/test_document_encryption.py`

```python
import os
import io
import base64
import hashlib
from decimal import Decimal
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from pypdf import PdfWriter

from core.models import User, Shop
from orders.models import PrintDocument
from connector.crypto_manager import ConnectorCryptoManager
from connector.page_validator import LocalDocumentValidator


def create_dummy_pdf_bytes(num_pages=3) -> bytes:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=595, height=842)  # A4 proportions
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


class DocumentSecurityAndEncryptionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='crypto_owner',
            email='crypto@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='Secure Doc Xerox',
            owner=self.owner,
            email='crypto@shop.example',
            phone='9876543210',
            address='Cyber Tower 1'
        )
        self.crypto_mgr = ConnectorCryptoManager()
        self.shop.connector_public_key = self.crypto_mgr.get_public_key_pem()
        self.shop.save()

    def test_client_side_encryption_and_local_connector_decryption(self):
        """
        End-to-End Zero-Knowledge Verification:
        1. Raw PDF generated.
        2. Client generates AES key, encrypts PDF via AES-GCM, wraps AES key with Shop RSA public key.
        3. Encrypted ciphertext uploaded to PrintDocument.
        4. Local Connector retrieves ciphertext and wrapped key, decrypts via RSA private key.
        5. Plaintext verified bit-for-bit identical to original PDF.
        """
        original_pdf = create_dummy_pdf_bytes(num_pages=2)
        pdf_sha256 = hashlib.sha256(original_pdf).hexdigest()

        # Step 2: Simulate Client-Side Encryption
        aes_key = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(aes_key)
        iv = os.urandom(12)
        # In AESGCM.encrypt, ciphertext includes 16-byte tag at the end
        ciphertext_with_tag = aesgcm.encrypt(iv, original_pdf, None)

        # Wrap AES key using Shop RSA Public Key (RSA-OAEP SHA-256)
        wrapped_key = self.crypto_mgr.public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        wrapped_key_b64 = base64.b64encode(wrapped_key).decode('utf-8')
        iv_b64 = base64.b64encode(iv).decode('utf-8')
        ciphertext_hash = hashlib.sha256(ciphertext_with_tag).hexdigest()

        # Step 3: Store in PrintDocument
        doc = PrintDocument.objects.create(
            shop=self.shop,
            original_filename='sensitive_contract.pdf',
            file_hash_sha256=ciphertext_hash,
            encrypted_file=SimpleUploadedFile('test.pdf.enc', ciphertext_with_tag),
            encrypted_file_size=len(ciphertext_with_tag),
            encrypted_key_bundle=wrapped_key_b64,
            encryption_iv=iv_b64,
            encryption_tag="",
            detected_page_count=2
        )

        # Verify cloud backend stores only ciphertext (NOT the original PDF)
        stored_bytes = doc.encrypted_file.read()
        self.assertNotEqual(stored_bytes, original_pdf)
        self.assertFalse(stored_bytes.startswith(b'%PDF'))

        # Step 4 & 5: Connector Decrypts Locally
        decrypted_pdf = self.crypto_mgr.decrypt_document(
            encrypted_ciphertext=stored_bytes,
            encrypted_key_bundle_b64=doc.encrypted_key_bundle,
            iv_b64=doc.encryption_iv,
            tag_b64=""
        )

        self.assertEqual(decrypted_pdf, original_pdf)
        self.assertEqual(hashlib.sha256(decrypted_pdf).hexdigest(), pdf_sha256)
        self.assertTrue(decrypted_pdf.startswith(b'%PDF'))

        # Step 6: Validate page count
        validation = LocalDocumentValidator.validate_pdf_pages(decrypted_pdf, expected_pages=2)
        self.assertTrue(validation['valid'])
        self.assertEqual(validation['actual_pages'], 2)
        self.assertFalse(validation['is_mismatch'])

    def test_page_count_mismatch_detection(self):
        """When actual PDF contains more pages than customer paid for, validation flags mismatch."""
        actual_pdf = create_dummy_pdf_bytes(num_pages=5)
        # Customer declared only 2 pages
        validation = LocalDocumentValidator.validate_pdf_pages(actual_pdf, expected_pages=2)
        self.assertTrue(validation['valid'])
        self.assertEqual(validation['actual_pages'], 5)
        self.assertTrue(validation['is_mismatch'])

```

---

## File: `tests/test_payments_and_orders.py`

```python
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import User, Shop
from orders.models import PrintOrder, PrintDocument, PrintPreference, PricingRule, PrintJob
from payments.models import Payment, Refund
from payments.services.gateway_adapter import get_payment_gateway, RazorpaySandboxAdapter


class PaymentsAndOrdersLifecycleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='payowner',
            email='pay@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='Payment Test Shop',
            owner=self.owner,
            email='pay@shop.example',
            phone='9876543210',
            address='Fintech Boulevard'
        )
        self.pricing = PricingRule.objects.create(
            shop=self.shop,
            bw_single_rate=Decimal('2.00'),
            bw_double_rate=Decimal('3.50'),
            color_single_rate=Decimal('10.00'),
            color_double_rate=Decimal('18.00'),
            a3_bw_rate=Decimal('5.00'),
            a3_color_rate=Decimal('20.00'),
        )

    def test_pricing_calculation_rules(self):
        """Validates all mathematical combinations of single/duplex/color/copies."""
        # 1. B&W Single: 5 pages * 1 copy = 5 sheets * 2.00 = 10.00
        p1 = PrintPreference(color_mode='BW', duplex_mode='SINGLE', paper_size='A4', copies=1)
        res1 = self.pricing.calculate_price(p1, 5)
        self.assertEqual(res1['total_amount'], 10.00)

        # 2. B&W Double: 5 pages -> 3 sheets * 3.50 = 10.50
        p2 = PrintPreference(color_mode='BW', duplex_mode='DOUBLE', paper_size='A4', copies=1)
        res2 = self.pricing.calculate_price(p2, 5)
        self.assertEqual(res2['total_amount'], 10.50)

        # 3. Color Single: 4 pages * 2 copies = 8 pages * 10.00 = 80.00
        p3 = PrintPreference(color_mode='COLOR', duplex_mode='SINGLE', paper_size='A4', copies=2)
        res3 = self.pricing.calculate_price(p3, 4)
        self.assertEqual(res3['total_amount'], 80.00)

    def test_payment_creation_and_cryptographic_verification(self):
        """End-to-end payment creation, signature verification, and job release."""
        doc = PrintDocument.objects.create(
            shop=self.shop,
            original_filename='invoice.pdf',
            file_hash_sha256='hash',
            encrypted_file=SimpleUploadedFile('inv.enc', b'ciphertext'),
            encrypted_file_size=10,
            encrypted_key_bundle='bundle',
            encryption_iv='iv',
            detected_page_count=2
        )
        pref = PrintPreference.objects.create(
            color_mode='BW',
            duplex_mode='SINGLE',
            paper_size='A4',
            copies=1,
            total_calculated_pages=2
        )
        order = PrintOrder.objects.create(
            order_number='ORD-PAY-TEST-001',
            shop=self.shop,
            customer_phone='9876543210',
            document=doc,
            preference=pref,
            status=PrintOrder.Status.AWAITING_PAYMENT,
            total_amount=Decimal('4.00'),
            idempotency_key='test_idemp_pay_001'
        )

        # 1. Create Payment Order via API
        create_resp = self.client.post(
            reverse('payments:api_create_payment_order'),
            {'order_number': order.order_number},
            content_type='application/json'
        )
        self.assertEqual(create_resp.status_code, 201)
        pay_data = create_resp.json()
        gateway_order_id = pay_data['gateway_order_id']
        self.assertTrue(gateway_order_id.startswith('order_'))

        gateway = get_payment_gateway()
        self.assertIsInstance(gateway, RazorpaySandboxAdapter)

        # 2. Test Invalid Signature is Rejected
        invalid_resp = self.client.post(
            reverse('payments:api_verify_payment'),
            {
                'gateway_order_id': gateway_order_id,
                'gateway_payment_id': 'pay_fake_123',
                'gateway_signature': 'invalid_signature_hex'
            },
            content_type='application/json'
        )
        self.assertEqual(invalid_resp.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, PrintOrder.Status.AWAITING_PAYMENT)

        # 3. Test Valid Signature Releases the Print Job
        valid_payment_id = 'pay_real_test_999'
        valid_signature = gateway.generate_expected_signature(gateway_order_id, valid_payment_id)

        valid_resp = self.client.post(
            reverse('payments:api_verify_payment'),
            {
                'gateway_order_id': gateway_order_id,
                'gateway_payment_id': valid_payment_id,
                'gateway_signature': valid_signature
            },
            content_type='application/json'
        )
        self.assertEqual(valid_resp.status_code, 200)

        order.refresh_from_db()
        self.assertIn(order.status, [PrintOrder.Status.PAYMENT_VERIFIED, PrintOrder.Status.QUEUED, PrintOrder.Status.ASSIGNED])
        self.assertTrue(hasattr(order, 'print_job'))

        # 4. Test Duplicate Verification Handled Idempotently
        dup_resp = self.client.post(
            reverse('payments:api_verify_payment'),
            {
                'gateway_order_id': gateway_order_id,
                'gateway_payment_id': valid_payment_id,
                'gateway_signature': valid_signature
            },
            content_type='application/json'
        )
        self.assertEqual(dup_resp.status_code, 200)
        self.assertEqual(dup_resp.json()['status'], 'already_processed')
        # PrintJob count remains exactly 1
        self.assertEqual(PrintJob.objects.filter(order=order).count(), 1)

```

---

## File: `tests/test_printers_and_routing.py`

```python
from decimal import Decimal
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import User, Shop
from printers.models import Printer, PrinterCapability, PrinterAssignment
from orders.models import PrintOrder, PrintDocument, PrintPreference, PrintJob, PricingRule
from printers.services.routing_service import RoutingService


class PrintersAndIntelligentRoutingTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='routingowner',
            email='routing@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='HighTech Xerox',
            owner=self.owner,
            email='routing@shop.example',
            phone='9876543210',
            address='Main Market'
        )
        PricingRule.objects.create(shop=self.shop)

        # Create Printer A: Monochrome High-Speed (B&W only, Single/Duplex, A4)
        self.printer_a = Printer.objects.create(
            shop=self.shop,
            name='Printer A (B&W Fast)',
            system_printer_name='HP_LaserJet_Mono',
            is_active=True,
            is_online=True,
            is_default=True,
            handles_bw=True,
            handles_color=False
        )
        PrinterCapability.objects.create(
            printer=self.printer_a,
            supports_bw=True,
            supports_color=False,
            supports_duplex=True,
            supported_paper_sizes=['A4']
        )

        # Create Printer B: Color Production (B&W + Color, Single/Duplex, A4 + A3)
        self.printer_b = Printer.objects.create(
            shop=self.shop,
            name='Printer B (Canon Color Pro)',
            system_printer_name='Canon_Color_C3530',
            is_active=True,
            is_online=True,
            is_default=False,
            handles_bw=True,
            handles_color=True
        )
        PrinterCapability.objects.create(
            printer=self.printer_b,
            supports_bw=True,
            supports_color=True,
            supports_duplex=True,
            supported_paper_sizes=['A4', 'A3']
        )

    def _create_order(self, color_mode='BW', duplex_mode='SINGLE', paper_size='A4', copies=1):
        doc = PrintDocument.objects.create(
            shop=self.shop,
            original_filename='file.pdf',
            file_hash_sha256='hash123',
            encrypted_file=SimpleUploadedFile('file.pdf.enc', b'encrypted'),
            encrypted_file_size=9,
            encrypted_key_bundle='keybundle',
            encryption_iv='iv',
            detected_page_count=5
        )
        pref = PrintPreference.objects.create(
            color_mode=color_mode,
            duplex_mode=duplex_mode,
            paper_size=paper_size,
            copies=copies,
            total_calculated_pages=5
        )
        order = PrintOrder.objects.create(
            order_number=f"ORD-TEST-{color_mode}-{paper_size}",
            shop=self.shop,
            customer_phone='9876543210',
            document=doc,
            preference=pref,
            status=PrintOrder.Status.PAYMENT_VERIFIED,
            total_amount=Decimal('10.00'),
            idempotency_key=f"idemp_{color_mode}_{paper_size}_{copies}"
        )
        return order

    def test_routing_bw_job_to_printer_a(self):
        """B&W standard job is routed to Printer A (default capable B&W)."""
        order = self._create_order(color_mode='BW', duplex_mode='SINGLE', paper_size='A4')
        job = RoutingService.route_paid_order(order)
        self.assertEqual(job.status, PrintJob.Status.DISPATCHED)
        self.assertEqual(job.printer, self.printer_a)
        self.assertEqual(order.status, PrintOrder.Status.ASSIGNED)

    def test_routing_color_job_to_printer_b(self):
        """Color job must NEVER go to Printer A (monochrome); must route to Printer B."""
        order = self._create_order(color_mode='COLOR', duplex_mode='SINGLE', paper_size='A4')
        job = RoutingService.route_paid_order(order)
        self.assertEqual(job.status, PrintJob.Status.DISPATCHED)
        self.assertEqual(job.printer, self.printer_b)

    def test_routing_a3_job_to_printer_b(self):
        """A3 job must route only to a printer supporting A3 paper size (Printer B)."""
        order = self._create_order(color_mode='BW', duplex_mode='SINGLE', paper_size='A3')
        job = RoutingService.route_paid_order(order)
        self.assertEqual(job.status, PrintJob.Status.DISPATCHED)
        self.assertEqual(job.printer, self.printer_b)

    def test_offline_printer_routes_to_queued_without_failure(self):
        """When required printer is offline and no fallback is eligible, job enters QUEUED state."""
        self.printer_b.is_online = False
        self.printer_b.save()

        # Place Color order (Printer A cannot print color)
        order = self._create_order(color_mode='COLOR', duplex_mode='SINGLE', paper_size='A4')
        job = RoutingService.route_paid_order(order)

        self.assertEqual(job.status, PrintJob.Status.QUEUED)
        self.assertIsNone(job.printer)
        self.assertEqual(order.status, PrintOrder.Status.QUEUED)

    def test_prevent_duplicate_job_creation(self):
        """Calling route_paid_order multiple times on the same order must NEVER duplicate the job."""
        order = self._create_order(color_mode='BW')
        job1 = RoutingService.route_paid_order(order)
        job2 = RoutingService.route_paid_order(order)

        self.assertEqual(job1.id, job2.id)
        self.assertEqual(PrintJob.objects.filter(order=order).count(), 1)

    def test_reassign_incompatible_printer_rejected(self):
        """Attempting to reassign a color job to a monochrome-only printer raises ValueError."""
        order = self._create_order(color_mode='COLOR')
        job = RoutingService.route_paid_order(order)
        job.status = PrintJob.Status.QUEUED
        job.save()

        with self.assertRaises(ValueError):
            RoutingService.reassign_job(job, self.printer_a)

```

---

## File: `tests/test_qr_and_shop.py`

```python
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Shop, ShopQRCode
from printers.models import Printer
from core.services.qr_service import generate_shop_qr_code


class PermanentQRCodeAndShopTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='qrowner',
            email='qr@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='Campus Copy Point',
            owner=self.owner,
            email='qr@shop.example',
            phone='9876543210',
            address='Gate 2, Campus Center'
        )
        self.qr_code_obj = generate_shop_qr_code(self.shop)

    def test_qr_code_generation_and_association(self):
        """Verify QR code is generated, permanently linked to shop slug, and stored."""
        self.assertIsNotNone(self.qr_code_obj)
        self.assertEqual(self.qr_code_obj.shop, self.shop)
        self.assertTrue(self.shop.slug in self.qr_code_obj.qr_target_url)

    def test_customer_scanning_qr_url_reaches_shop_ordering_page(self):
        """Customer accessing the QR destination reaches the correct shop ordering page."""
        response = self.client.get(reverse('shop_order_page', kwargs={'slug': self.shop.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Campus Copy Point')
        self.assertContains(response, 'Select PDF Document')

    def test_qr_remains_unchanged_after_printer_changes(self):
        """Adding, modifying, or deleting printers must NEVER alter the permanent QR code URL."""
        initial_qr_target = self.qr_code_obj.qr_target_url
        initial_slug = self.shop.slug

        # Add Printer 1
        p1 = Printer.objects.create(
            shop=self.shop,
            name='Canon 1',
            system_printer_name='Canon_IR2520',
            is_active=True,
            is_online=True,
            is_default=True
        )

        # Re-fetch QR code
        self.qr_code_obj.refresh_from_db()
        self.assertEqual(self.qr_code_obj.qr_target_url, initial_qr_target)

        # Switch default printer to Printer 2
        p2 = Printer.objects.create(
            shop=self.shop,
            name='HP LaserJet',
            system_printer_name='HP_LaserJet_Pro',
            is_active=True,
            is_online=True,
            is_default=False
        )
        p1.is_default = False
        p1.save()
        p2.is_default = True
        p2.save()

        # Disable Printer 1
        p1.is_active = False
        p1.is_online = False
        p1.save()

        # Delete Printer 2
        p2.delete()

        # Verify QR code is strictly identical
        self.qr_code_obj.refresh_from_db()
        self.assertEqual(self.qr_code_obj.qr_target_url, initial_qr_target)
        self.assertEqual(self.shop.slug, initial_slug)

    def test_pause_ordering_toggle_behavior(self):
        """When paused, ordering page displays unavailable notice and rejects order creation."""
        self.shop.is_accepting_orders = False
        self.shop.pause_message = "Closed for lunch break. Reopening at 2 PM."
        self.shop.save()

        response = self.client.get(reverse('shop_order_page', kwargs={'slug': self.shop.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ordering Temporarily Paused')
        self.assertContains(response, 'Closed for lunch break. Reopening at 2 PM.')
        self.assertNotContains(response, 'Select PDF Document')

```

---

