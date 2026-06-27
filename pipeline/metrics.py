import threading
from typing import Dict

class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._processed = 0
        self._dropped = 0
        self._alerts = 0

    def update(self, processed: int = 0, dropped: int = 0, alerts: int = 0) -> None:
        with self._lock:
            self._processed += processed
            self._dropped += dropped
            self._alerts += alerts

    def get_and_reset_throughput(self) -> int:
        with self._lock:
            throughput = self._processed
            self._processed = 0
            return throughput

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                "dropped": self._dropped,
                "alerts": self._alerts
            }