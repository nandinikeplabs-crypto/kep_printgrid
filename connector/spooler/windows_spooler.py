import os
import sys
import subprocess
import logging
from .base_spooler import BaseSpooler

logger = logging.getLogger("PrintGridConnector.WindowsSpooler")


class WindowsSpooler(BaseSpooler):
    """
    Windows Print Spooler Integration using pywin32 / PowerShell PrintTo.
    """
    def __init__(self):
        self.has_win32print = False
        try:
            import win32print
            import win32api
            self.win32print = win32print
            self.win32api = win32api
            self.has_win32print = True
            logger.info("Native win32print spooler integration loaded successfully.")
        except ImportError:
            logger.warning("pywin32 (win32print) is not installed. Windows PowerShell spooler commands will be used.")

    def get_installed_printers(self) -> list:
        printers = []
        if self.has_win32print:
            try:
                flags = self.win32print.PRINTER_ENUM_LOCAL | self.win32print.PRINTER_ENUM_CONNECTIONS
                enum_list = self.win32print.EnumPrinters(flags)
                default_name = self.win32print.GetDefaultPrinter()

                for p in enum_list:
                    # p is a tuple: (flags, description, name, comment)
                    name = p[2]
                    is_default = (name == default_name)

                    # Inspect basic capabilities
                    is_color = any(k in name.lower() for k in ["color", "cmyk", "tank", "deskjet", "inkjet", "photosmart", "officejet", "epson l", "canon g", "smart tank"])
                    supports_a3 = "a3" in name.lower() or "wide" in name.lower()
                    paper_sizes = ['A4']
                    if supports_a3:
                        paper_sizes.append('A3')

                    printers.append({
                        'system_name': name,
                        'friendly_name': name,
                        'is_online': True,
                        'is_default': is_default,
                        'status': 'Ready',
                        'capabilities': {
                            'supports_bw': True,
                            'supports_color': is_color,
                            'supports_duplex': True,
                            'supported_paper_sizes': paper_sizes,
                            'supports_landscape': True,
                            'dpi': 600
                        }
                    })
                if printers:
                    return printers
            except Exception as e:
                logger.error(f"Error enumerating printers via win32print: {e}")

        # Fallback via PowerShell Get-Printer
        try:
            cmd = "Get-Printer | Select-Object Name, PrinterStatus, Default | ConvertTo-Json"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get('Name', '')
                    if not name:
                        continue
                    is_color = any(k in name.lower() for k in ["color", "cmyk", "tank", "deskjet", "inkjet", "photosmart", "officejet", "epson l", "canon g", "smart tank"])
                    is_a3 = "a3" in name.lower()
                    paper_sizes = ['A4']
                    if is_a3:
                        paper_sizes.append('A3')

                    printers.append({
                        'system_name': name,
                        'friendly_name': name,
                        'is_online': True,
                        'is_default': bool(item.get('Default', False)),
                        'status': 'Ready',
                        'capabilities': {
                            'supports_bw': True,
                            'supports_color': is_color,
                            'supports_duplex': True,
                            'supported_paper_sizes': paper_sizes,
                            'supports_landscape': True,
                            'dpi': 600
                        }
                    })
        except Exception as e:
            logger.error(f"Error querying PowerShell Get-Printer: {e}")

        # If no physical printer configured, provide standard Microsoft Print to PDF printer
        if not printers:
            printers.append({
                'system_name': 'Microsoft Print to PDF',
                'friendly_name': 'Microsoft Print to PDF (Windows Virtual Spooler)',
                'is_online': True,
                'is_default': True,
                'status': 'Ready',
                'capabilities': {
                    'supports_bw': True,
                    'supports_color': True,
                    'supports_duplex': True,
                    'supported_paper_sizes': ['A4', 'A3'],
                    'supports_landscape': True,
                    'dpi': 600
                }
            })
        return printers

    def _resolve_real_printer_name(self, requested_name: str) -> str:
        """Finds the best matching installed printer name on Windows."""
        try:
            installed = self.get_installed_printers()
            if not installed:
                return requested_name

            # 1. Exact match
            for p in installed:
                if p['system_name'].lower() == requested_name.lower():
                    return p['system_name']

            # 2. Substring match (e.g. 'HP Smart Tank 530' matches 'HP Smart Tank 530 series')
            for p in installed:
                if requested_name.lower() in p['system_name'].lower() or p['system_name'].lower() in requested_name.lower():
                    return p['system_name']

            # 3. Keyword match (e.g. '530' or 'smart tank')
            keywords = [w for w in requested_name.lower().split() if len(w) > 2]
            for p in installed:
                if any(k in p['system_name'].lower() for k in keywords):
                    return p['system_name']

            # 4. Fallback to default printer
            for p in installed:
                if p.get('is_default'):
                    return p['system_name']

            return installed[0]['system_name']
        except Exception:
            return requested_name

    def submit_print_job(self, printer_name: str, pdf_path: str, preferences: dict) -> dict:
        if not os.path.exists(pdf_path):
            return {'success': False, 'os_job_id': '', 'message': f"PDF path does not exist: {pdf_path}"}

        # Resolve real system printer name
        actual_printer = self._resolve_real_printer_name(printer_name)
        logger.info(f"Resolved printer '{printer_name}' -> system printer '{actual_printer}'")

        # Check if native win32print raw spool submission is applicable
        if self.has_win32print:
            try:
                h_printer = self.win32print.OpenPrinter(actual_printer)
                job_id = self.win32print.StartDocPrinter(h_printer, 1, (f"KEP_PrintGrid_{os.path.basename(pdf_path)}", None, "RAW"))
                self.win32print.StartPagePrinter(h_printer)
                with open(pdf_path, 'rb') as f:
                    self.win32print.WritePrinter(h_printer, f.read())
                self.win32print.EndPagePrinter(h_printer)
                self.win32print.EndDocPrinter(h_printer)
                self.win32print.ClosePrinter(h_printer)
                return {
                    'success': True,
                    'os_job_id': str(job_id),
                    'message': f"Submitted to Windows spooler printer '{actual_printer}'"
                }
            except Exception as e:
                logger.warning(f"win32print direct spool failed ({e}), falling back to Windows PrintTo verb.")

        # Fallback via PowerShell Start-Process PrintTo
        try:
            escaped_pdf = pdf_path.replace("'", "''")
            escaped_printer = actual_printer.replace("'", "''")
            cmd = f"Start-Process -FilePath '{escaped_pdf}' -Verb PrintTo -ArgumentList '\"{escaped_printer}\"' -PassThru"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                return {
                    'success': True,
                    'os_job_id': f"PS_{os.path.basename(pdf_path)}",
                    'message': f"Dispatched via Windows shell PrintTo to '{actual_printer}'"
                }
            else:
                return {
                    'success': False,
                    'os_job_id': '',
                    'message': f"Print command returned exit code {res.returncode}: {res.stderr}"
                }
        except Exception as e:
            return {'success': False, 'os_job_id': '', 'message': str(e)}

    def check_job_status(self, printer_name: str, os_job_id: str) -> dict:
        if self.has_win32print and os_job_id.isdigit():
            try:
                h_printer = self.win32print.OpenPrinter(printer_name)
                job_info = self.win32print.GetJob(h_printer, int(os_job_id), 1)
                self.win32print.ClosePrinter(h_printer)
                status_flags = job_info.get('Status', 0)
                return {
                    'exists': True,
                    'status_flags': status_flags,
                    'is_completed': status_flags == 0
                }
            except Exception:
                # If GetJob fails because job finished and was removed from queue, it is completed
                return {'exists': False, 'is_completed': True}

        return {'exists': True, 'is_completed': True}
