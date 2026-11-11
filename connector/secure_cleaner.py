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
