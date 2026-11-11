import sys
import os
from .base_spooler import BaseSpooler
from .windows_spooler import WindowsSpooler
from .dev_spooler import DevSpooler


def get_spooler(force_mode: str = None) -> BaseSpooler:
    """
    Returns the appropriate print spooler interface.
    Auto-detects Windows or falls back to DevSpooler.
    """
    mode = force_mode or os.environ.get('CONNECTOR_SPOOLER_MODE', 'auto')

    if mode == 'dev':
        return DevSpooler()
    elif mode == 'windows' or (mode == 'auto' and sys.platform.startswith('win')):
        return WindowsSpooler()
    return DevSpooler()
