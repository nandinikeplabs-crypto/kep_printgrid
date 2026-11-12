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

    p_draw.text((poster_w // 2, 370), shop.name.upper(), fill="#0F172A", anchor="mm")
    p_draw.text((poster_w // 2, 415), f"SHOP ID: {shop.shop_code or shop.slug}", fill="#2563EB", anchor="mm")
    p_draw.text((poster_w // 2, 455), f"Address: {shop.address[:60]}", fill="#64748B", anchor="mm")

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
