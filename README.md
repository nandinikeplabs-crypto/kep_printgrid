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
