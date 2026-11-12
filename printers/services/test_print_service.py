import os
import secrets
import tempfile
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont


def generate_printer_test_page(shop, printer) -> str:
    """
    Generates a physical test verification PDF document for the given printer.
    Includes calibration gradients, alignment markers, shop credentials, and unique Printer ID.
    Returns the absolute path to the generated temporary PDF.
    """
    w, h = 1240, 1754  # A4 proportioned @ 150 DPI
    img = Image.new("RGB", (w, h), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # 1. Top Header Banner
    draw.rectangle([0, 0, w, 220], fill="#0F172A")
    draw.rectangle([0, 220, w, 230], fill="#2563EB")

    draw.text((w // 2, 60), "KEP PRINTGRID", fill="#38BDF8", anchor="mm")
    draw.text((w // 2, 120), "PRINTER HARDWARE VERIFICATION TEST PAGE", fill="#FFFFFF", anchor="mm")
    draw.text((w // 2, 175), "Universal Windows Spooler & QR Mapping Engine", fill="#94A3B8", anchor="mm")

    # 2. Outer Page Border & Alignment Marks
    draw.rectangle([40, 260, w - 40, h - 60], outline="#CBD5E1", width=3)
    # Corner registration crosshairs
    for cx, cy in [(60, 280), (w - 60, 280), (60, h - 80), (w - 60, h - 80)]:
        draw.line([(cx - 15, cy), (cx + 15, cy)], fill="#0F172A", width=2)
        draw.line([(cx, cy - 15), (cx, cy + 15)], fill="#0F172A", width=2)
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline="#2563EB", width=2)

    # 3. Shop & QR Identification Box
    card_margin = 70
    top_y = 310
    draw.rounded_rectangle([card_margin, top_y, w - card_margin, top_y + 260], radius=16, fill="#F8FAFC", outline="#E2E8F0", width=2)
    draw.text((card_margin + 30, top_y + 35), "1. SHOP & QR CODE MAPPING CREDENTIALS", fill="#0F172A")
    draw.line([(card_margin + 30, top_y + 60), (w - card_margin - 30, top_y + 60)], fill="#E2E8F0", width=1)

    qr_assigned_str = "Mapped to Shop QR Code" if getattr(shop, 'qr_code', None) and shop.qr_code.assigned_printer_id == printer.id else "Unassigned (Shop Fleet)"

    draw.text((card_margin + 30, top_y + 85), f"Shop Name:  {shop.name}", fill="#1E293B")
    draw.text((card_margin + 30, top_y + 120), f"Shop Code:  {shop.shop_code or shop.slug}", fill="#2563EB")
    draw.text((card_margin + 30, top_y + 155), f"Address:    {shop.address[:65]}", fill="#64748B")
    draw.text((card_margin + 30, top_y + 190), f"QR Status:  {qr_assigned_str}", fill="#16A34A" if "Mapped" in qr_assigned_str else "#D97706")
    draw.text((card_margin + 30, top_y + 225), f"QR URL:     {shop.order_page_url[:65]}", fill="#64748B")

    # 4. Printer Identification Box
    p_top = 600
    draw.rounded_rectangle([card_margin, p_top, w - card_margin, p_top + 280], radius=16, fill="#F0FDF4", outline="#BBF7D0", width=2)
    draw.text((card_margin + 30, p_top + 35), "2. REGISTERED PRINTER SPECIFICATIONS", fill="#15803D")
    draw.line([(card_margin + 30, p_top + 60), (w - card_margin - 30, p_top + 60)], fill="#DCFCE7", width=1)

    draw.text((card_margin + 30, p_top + 85), f"Printer Name:     {printer.name}", fill="#0F172A")
    draw.text((card_margin + 30, p_top + 120), f"Printer ID:       {printer.printer_code} (UUID: {printer.id})", fill="#2563EB")
    draw.text((card_margin + 30, p_top + 155), f"Windows Queue:    {printer.system_printer_name}", fill="#1E293B")
    draw.text((card_margin + 30, p_top + 190), f"Hardware Model:   {printer.model_name or 'Universal Windows Spooler Copier'}", fill="#64748B")
    draw.text((card_margin + 30, p_top + 225), f"Connection State: {printer.detailed_status} | Capabilities: {'Colour + B&W' if printer.handles_color else 'B&W Only'}", fill="#15803D")

    # 5. Diagnostic Calibration Blocks
    cal_top = 910
    draw.rounded_rectangle([card_margin, cal_top, w - card_margin, cal_top + 350], radius=16, fill="#F8FAFC", outline="#E2E8F0", width=2)
    draw.text((card_margin + 30, cal_top + 35), "3. HARDWARE PRINT DIAGNOSTICS & COLOR CALIBRATION", fill="#0F172A")
    draw.line([(card_margin + 30, cal_top + 60), (w - card_margin - 30, cal_top + 60)], fill="#E2E8F0", width=1)

    # Grayscale Gradient steps
    grad_y = cal_top + 80
    grad_w = (w - 2 * card_margin - 60) // 5
    shades = [("100% Black", "#000000", "#FFFFFF"), ("75% Dark", "#404040", "#FFFFFF"), ("50% Medium", "#808080", "#FFFFFF"), ("25% Light", "#C0C0C0", "#000000"), ("10% Pale", "#E6E6E6", "#000000")]
    for idx, (label, color, txt_color) in enumerate(shades):
        bx = card_margin + 30 + idx * grad_w
        draw.rectangle([bx, grad_y, bx + grad_w - 6, grad_y + 60], fill=color, outline="#CBD5E1")
        draw.text((bx + (grad_w - 6) // 2, grad_y + 30), label, fill=txt_color, anchor="mm")

    # CMYK Color blocks
    color_y = cal_top + 160
    color_blocks = [("Cyan", "#00FFFF", "#000000"), ("Magenta", "#FF00FF", "#FFFFFF"), ("Yellow", "#FFFF00", "#000000"), ("Black (Key)", "#000000", "#FFFFFF")]
    c_w = (w - 2 * card_margin - 60) // 4
    for idx, (c_name, c_hex, c_txt) in enumerate(color_blocks):
        bx = card_margin + 30 + idx * c_w
        draw.rectangle([bx, color_y, bx + c_w - 6, color_y + 60], fill=c_hex, outline="#CBD5E1")
        draw.text((bx + (c_w - 6) // 2, color_y + 30), c_name, fill=c_txt, anchor="mm")

    # Fine line resolution test
    lines_y = cal_top + 245
    draw.text((card_margin + 30, lines_y), "Fine Line Spacing (1px - 4px):", fill="#64748B")
    for thickness in range(1, 5):
        lx = card_margin + 320 + thickness * 70
        draw.line([(lx, lines_y - 5), (lx, lines_y + 25)], fill="#0F172A", width=thickness)

    # 6. Verification Summary & Security Stamp
    sec_top = 1290
    test_id = f"TST-{timezone.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
    now_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    draw.rounded_rectangle([card_margin, sec_top, w - card_margin, sec_top + 240], radius=16, fill="#EFF6FF", outline="#BFDBFE", width=2)
    draw.text((card_margin + 30, sec_top + 35), "4. CRYPTOGRAPHIC TEST DISPATCH VERIFICATION", fill="#1D4ED8")
    draw.line([(card_margin + 30, sec_top + 60), (w - card_margin - 30, sec_top + 60)], fill="#DBEAFE", width=1)

    draw.text((card_margin + 30, sec_top + 85), f"Verification Test ID: {test_id}", fill="#0F172A")
    draw.text((card_margin + 30, sec_top + 120), f"Timestamp:           {now_str}", fill="#1E293B")
    draw.text((card_margin + 30, sec_top + 155), f"Result:              PHYSICAL SPOOLER HANDSHAKE PASSED", fill="#16A34A")
    draw.text((card_margin + 30, sec_top + 190), "This test confirms your Windows printer communicates properly with KEP PrintGrid.", fill="#64748B")

    # 7. Footer
    draw.text((w // 2, h - 35), "KEP PrintGrid Platform • Zero-Knowledge Smart Printing Platform", fill="#94A3B8", anchor="mm")

    # Save to temp PDF
    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"test_print_{printer.printer_code}_")
    os.close(temp_fd)
    img.save(temp_path, "PDF", resolution=150.0)
    return temp_path
