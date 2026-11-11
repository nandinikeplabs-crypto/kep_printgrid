from abc import ABC, abstractmethod


class BaseSpooler(ABC):
    @abstractmethod
    def get_installed_printers(self) -> list:
        """
        Returns a list of dicts describing available printers and capabilities:
        [
            {
                'system_name': '...',
                'friendly_name': '...',
                'is_online': True,
                'status': 'Ready',
                'capabilities': {
                    'supports_bw': True,
                    'supports_color': False,
                    'supports_duplex': True,
                    'supported_paper_sizes': ['A4', 'A3'],
                    'supports_landscape': True,
                    'dpi': 600
                }
            }
        ]
        """
        pass

    @abstractmethod
    def submit_print_job(self, printer_name: str, pdf_path: str, preferences: dict) -> dict:
        """
        Submits the physical job to the OS print spooler.
        Returns dict with:
        {
            'success': bool,
            'os_job_id': str,
            'message': str
        }
        """
        pass

    @abstractmethod
    def check_job_status(self, printer_name: str, os_job_id: str) -> dict:
        """
        Queries the OS spooler for the true status of the submitted print job.
        """
        pass
