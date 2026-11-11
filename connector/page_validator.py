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
