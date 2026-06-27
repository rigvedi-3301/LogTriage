import json
import queue
import random
import threading
import time
from datetime import datetime, timezone
from pipeline.metrics import Metrics

class LogProducer(threading.Thread):
    def __init__(self, log_queue: queue.Queue, metrics: Metrics, shutdown_event: threading.Event) -> None:
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.metrics = metrics
        self.shutdown_event = shutdown_event
        self.services = ["auth-service", "payment-gateway", "user-profile", "search-engine"]
        self.levels = ["INFO", "INFO", "INFO", "WARN", "ERROR", "CRITICAL"]

    def run(self) -> None:
        msg = "transaction processed successfully or failed miserably"
        while not self.shutdown_event.is_set():
            now = datetime.now(timezone.utc).isoformat()
            level = random.choice(self.levels)
            service = random.choice(self.services)
            
            log_entry = f'{{"timestamp": "{now}", "level": "{level}", "service": "{service}", "message": "{msg}"}}'
            
            try:
                self.log_queue.put_nowait(log_entry)
            except queue.Full:
                self.metrics.update(dropped=1)
                time.sleep(0.001)

class LogConsumer(threading.Thread):
    def __init__(self, log_queue: queue.Queue, alert_queue: queue.Queue, metrics: Metrics, shutdown_event: threading.Event) -> None:
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.alert_queue = alert_queue
        self.metrics = metrics
        self.shutdown_event = shutdown_event

    def run(self) -> None:
        local_processed = 0
        local_alerts = 0
        
        while not self.shutdown_event.is_set() or not self.log_queue.empty():
            try:
                log_raw = self.log_queue.get(timeout=0.1)
            except queue.Empty:
                continue
                
            try:
                log_data = json.loads(log_raw)
                if log_data.get("level") in ("ERROR", "CRITICAL"):
                    self.alert_queue.put_nowait(log_data)
                    local_alerts += 1
            except (json.JSONDecodeError, queue.Full):
                pass
            finally:
                self.log_queue.task_done()
                local_processed += 1
                
                if local_processed >= 100:
                    self.metrics.update(processed=local_processed, alerts=local_alerts)
                    local_processed = 0
                    local_alerts = 0
                    
        if local_processed > 0 or local_alerts > 0:
            self.metrics.update(processed=local_processed, alerts=local_alerts)