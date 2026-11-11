import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("PrintGridConnector.LocalStore")


class LocalExecutionStore:
    """
    Maintains a persistent ledger of jobs processed locally
    to prevent duplicate physical prints.
    """
    def __init__(self, store_path=None):
        if not store_path:
            store_path = os.path.join(os.path.dirname(__file__), "local_execution_log.json")
        self.store_path = store_path
        self._cache = self._load()

    def _load(self):
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading local execution log: {e}")
        return {}

    def _save(self):
        try:
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving local execution log: {e}")

    def is_job_executed(self, job_id: str) -> bool:
        return job_id in self._cache and self._cache[job_id].get('status') == 'COMPLETED'

    def record_job(self, job_id: str, printer: str, status: str, details: str = ""):
        self._cache[job_id] = {
            'printer': printer,
            'status': status,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self._save()
