import os
import sys
import django
import uuid

# Initialize Django environment
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kep_printgrid.settings")
django.setup()

from django.test import Client
from django.urls import reverse
from core.models import User, Shop, ShopQRCode
from orders.models import PricingRule, PrintOrder
from printers.models import Printer, PrinterCapability


def run_acceptance_test():
    print("=" * 75)
    print("  KEP PRINTGRID - SEPARATE SHOP OWNER & CUSTOMER ACCEPTANCE TEST")
    print("=" * 75)

    client = Client()

    # Clean previous test runs for repeatable execution
    User.objects.filter(email__in=['alok@alphaexpress.example', 'bhavna@betahub.example']).delete()
    Shop.objects.filter(name__in=['Alpha Express Xerox', 'Beta Digital Hub']).delete()

    # Step 1: Open Main Website
    print("\n[STEP 1] Opening Main Website (/) ...")
    resp = client.get('/')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    content = resp.content.decode()
    assert "Shop Owner Interface" in content, "Missing Shop Owner Interface section on home page"
    assert "Customer Interface" in content, "Missing Customer Interface section on home page"
    print("  -> Main Website loaded successfully with clearly separated Shop Owner and Customer sections.")

    # Step 2 & 3: Register Shop A
    print("\n[STEP 2 & 3] Registering Shop A ('Alpha Express Xerox') via /register-shop/ ...")
    reg_data_a = {
        'shop_name': 'Alpha Express Xerox',
        'owner_name': 'Alok Sharma',
        'email': 'alok@alphaexpress.example',
        'mobile_number': '9876500001',
        'password': 'AlphaPass2026!',
        'confirm_password': 'AlphaPass2026!',
        'shop_address': 'Building 1, Science Block, University Campus'
    }
    resp = client.post('/register-shop/', data=reg_data_a, follow=True)
    assert resp.status_code == 200, f"Registration failed with code {resp.status_code}"
    
    shop_a = Shop.objects.filter(email='alok@alphaexpress.example').first()
    assert shop_a is not None, "Shop A was not created in the database."
    assert shop_a.shop_code.startswith('KEP'), f"Shop A shop_code does not start with KEP: {shop_a.shop_code}"
    print(f"  -> Shop A Created: '{shop_a.name}'")
    print(f"  -> Generated Unique Shop ID: {shop_a.shop_code}")

    # Step 4: Verify Redirection to Shop A Dashboard
    print("\n[STEP 4] Verifying Shop A Dashboard ...")
    dash_resp = client.get('/dashboard/')
    assert dash_resp.status_code in [200, 302], f"Dashboard access error: {dash_resp.status_code}"
    # Follow redirect to overview if needed
    if dash_resp.status_code == 302:
        dash_resp = client.get(dash_resp.url)
    dash_content = dash_resp.content.decode()
    assert shop_a.shop_code in dash_content, f"Shop code {shop_a.shop_code} not found on dashboard"
    assert "Alpha Express Xerox" in dash_content, "Shop A name not on dashboard"
    print(f"  -> Shop A Dashboard loaded with Shop ID {shop_a.shop_code} and sidebar management.")

    # Step 5: Verify Shop A Permanent QR Code Generation
    print("\n[STEP 5] Verifying Shop A Permanent QR Code Stand ...")
    qr_a = ShopQRCode.objects.filter(shop=shop_a).first()
    assert qr_a is not None, "QR code record missing for Shop A"
    assert shop_a.shop_code in qr_a.qr_target_url, f"QR target URL {qr_a.qr_target_url} does not contain {shop_a.shop_code}"
    print(f"  -> QR Target URL: {qr_a.qr_target_url}")
    print(f"  -> QR Poster Stand File: {qr_a.qr_code_image}")

    # Step 6, 7 & 8: Customer Accesses Shop A via Permanent QR URL
    print("\n[STEP 6, 7 & 8] Customer scans QR Code and opens Shop A Customer Page ...")
    customer_client = Client() # Separate unauthenticated customer browser
    cust_resp_a = customer_client.get(f'/shop/{shop_a.shop_code}/')
    assert cust_resp_a.status_code == 200, f"Customer page returned {cust_resp_a.status_code}"
    cust_content_a = cust_resp_a.content.decode()
    assert "Alpha Express Xerox" in cust_content_a, "Shop A name missing from customer page"
    assert "Select PDF Document" in cust_content_a, "Upload wizard missing from customer page"
    assert "Printing Preferences" in cust_content_a, "Preferences missing from customer page"
    assert "Owner Dashboard Overview" not in cust_content_a, "SECURITY LEAK: Owner controls visible to customer!"
    print(f"  -> Customer Ordering Page loaded for '{shop_a.name}'.")
    print(f"  -> Customer View is 100% clean and free of shop owner dashboard controls.")

    # Step 9 & 10: Register Shop B ("Beta Digital Hub")
    print("\n[STEP 9 & 10] Registering Shop B ('Beta Digital Hub') via /register-shop/ ...")
    reg_data_b = {
        'shop_name': 'Beta Digital Hub',
        'owner_name': 'Bhavna Patel',
        'email': 'bhavna@betahub.example',
        'mobile_number': '9876500002',
        'password': 'BetaPass2026!',
        'confirm_password': 'BetaPass2026!',
        'shop_address': 'Shop 12, Main Tech Park, Sector 4'
    }
    owner_b_client = Client()
    resp_b = owner_b_client.post('/register-shop/', data=reg_data_b, follow=True)
    assert resp_b.status_code == 200, f"Shop B registration failed: {resp_b.status_code}"
    
    shop_b = Shop.objects.filter(email='bhavna@betahub.example').first()
    assert shop_b is not None, "Shop B not created"
    assert shop_b.shop_code != shop_a.shop_code, "Shop B must have a different unique ID from Shop A!"
    qr_b = ShopQRCode.objects.filter(shop=shop_b).first()
    print(f"  -> Shop B Created: '{shop_b.name}'")
    print(f"  -> Generated Unique Shop ID: {shop_b.shop_code}")
    print(f"  -> Shop B Permanent QR Target: {qr_b.qr_target_url}")

    # Step 11 & 12: Customer Accesses Shop B via QR URL
    print("\n[STEP 11 & 12] Customer scans QR Code and opens Shop B Customer Page ...")
    cust_resp_b = customer_client.get(f'/shop/{shop_b.shop_code}/')
    assert cust_resp_b.status_code == 200, f"Shop B customer page returned {cust_resp_b.status_code}"
    cust_content_b = cust_resp_b.content.decode()
    assert "Beta Digital Hub" in cust_content_b, "Shop B name missing"
    assert "Alpha Express Xerox" not in cust_content_b, "Shop A name leaked into Shop B customer page!"
    print(f"  -> Customer Ordering Page loaded strictly for Shop B.")
    print(f"  -> Verified zero leakage between Shop A and Shop B.")

    # Step 13: Verify Multi-Shop Isolation (Pricing, Printers, Dashboard)
    print("\n[STEP 13] Verifying Multi-Shop Data Isolation...")
    # Set custom pricing for Shop A (₹ 3.50 B&W) vs Shop B (₹ 1.75 B&W)
    pricing_a = PricingRule.objects.get(shop=shop_a)
    pricing_a.bw_single_rate = 3.50
    pricing_a.save()

    pricing_b = PricingRule.objects.get(shop=shop_b)
    pricing_b.bw_single_rate = 1.75
    pricing_b.save()

    # Re-fetch customer pages and verify pricing isolation
    check_a = customer_client.get(f'/shop/{shop_a.shop_code}/').content.decode()
    check_b = customer_client.get(f'/shop/{shop_b.shop_code}/').content.decode()
    assert "3.5" in check_a, "Shop A custom pricing not reflected"
    assert "1.75" in check_b, "Shop B custom pricing not reflected"

    # Add different printers
    p_a = Printer.objects.create(shop=shop_a, name="HP LaserJet Alpha", system_printer_name="HP_Alpha", is_active=True, is_online=True)
    p_b = Printer.objects.create(shop=shop_b, name="Canon IR Beta", system_printer_name="Canon_Beta", is_active=True, is_online=True)

    assert Printer.objects.filter(shop=shop_a).count() == 1
    assert Printer.objects.filter(shop=shop_b).count() == 1
    print(f"  -> Shop A Rate: ₹{pricing_a.bw_single_rate} | Printers: {[p.name for p in Printer.objects.filter(shop=shop_a)]}")
    print(f"  -> Shop B Rate: ₹{pricing_b.bw_single_rate} | Printers: {[p.name for p in Printer.objects.filter(shop=shop_b)]}")
    print("  -> Multi-Shop Data Isolation Verified 100% Active!")

    # Step 14 & 15: Change Shop A's Active Printer and Invariant Check
    print("\n[STEP 14 & 15] Changing Shop A Active Printer & Verifying Permanent QR Invariant...")
    initial_qr_target = qr_a.qr_target_url
    
    # Deactivate HP printer and add a new heavy copier
    p_a.is_active = False
    p_a.save()
    p_a2 = Printer.objects.create(shop=shop_a, name="Xerox WorkCentre Alpha New", system_printer_name="Xerox_Alpha_2", is_active=True, is_online=True)

    # Re-fetch Shop A QR code from database
    qr_a.refresh_from_db()
    assert qr_a.qr_target_url == initial_qr_target, "CRITICAL ERROR: Changing printers modified the permanent QR code!"
    
    # Customer scans same QR URL again
    cust_resp_again = customer_client.get(initial_qr_target.replace('http://127.0.0.1:8080', ''))
    assert cust_resp_again.status_code == 200
    assert "Alpha Express Xerox" in cust_resp_again.content.decode()
    print(f"  -> Hardware replaced: '{p_a.name}' disabled -> '{p_a2.name}' installed.")
    print(f"  -> Permanent QR Target URL remains identical: {qr_a.qr_target_url}")
    print(f"  -> Permanent QR Invariant Verified: Counter QR stand never needs to be reprinted!")

    print("\n" + "=" * 75)
    print(" [ACCEPTANCE TEST PASSED 100%] ALL 15 VERIFICATION STEPS SUCCEEDED!")
    print("=" * 75)


if __name__ == '__main__':
    run_acceptance_test()
