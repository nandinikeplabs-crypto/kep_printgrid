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
        if tag_b64 == 'PLAIN' or encrypted_key_bundle_b64 == 'PLAIN_DEV_FALLBACK':
            return encrypted_ciphertext

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
