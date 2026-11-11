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
