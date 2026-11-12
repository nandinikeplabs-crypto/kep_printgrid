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
            from urllib.parse import urlparse, urlunparse
            parsed_dl = urlparse(download_url)
            parsed_srv = urlparse(self.server_url)
            local_dl_url = urlunparse((parsed_srv.scheme, parsed_srv.netloc, parsed_dl.path, '', parsed_dl.query, ''))

            try:
                file_resp = requests.get(local_dl_url, timeout=20)
            except Exception:
                file_resp = requests.get(download_url, timeout=20)

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
