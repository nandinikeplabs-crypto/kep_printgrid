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
