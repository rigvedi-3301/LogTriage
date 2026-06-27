import queue
import threading
from pipeline.metrics import Metrics
from pipeline.workers import LogProducer, LogConsumer
from pipeline.reporter import WebSocketMetricsReporter
from pipeline.analyzer import AlertWindowProcessor

class LogParsingEngine:
    def __init__(self) -> None:
        self.shutdown_event = threading.Event()
        self.metrics = Metrics()
        self.log_queue = queue.Queue(maxsize=10000)
        self.alert_queue = queue.Queue()
        self.ai_summary_queue = queue.Queue()
        
        self.producer = LogProducer(self.log_queue, self.metrics, self.shutdown_event)
        self.consumers = [
            LogConsumer(self.log_queue, self.alert_queue, self.metrics, self.shutdown_event) 
            for _ in range(4)
        ]
        self.ws_reporter = WebSocketMetricsReporter(
            self.log_queue, self.alert_queue, self.metrics, self.ai_summary_queue, self.shutdown_event
        )
        self.alert_processor = AlertWindowProcessor(
            self.alert_queue, self.ai_summary_queue, self.shutdown_event
        )

    def start(self) -> None:
        print("[SYSTEM] Starting Log Parsing Engine...")
        self.ws_reporter.start()
        self.alert_processor.start()
        
        for consumer in self.consumers:
            consumer.start()
            
        self.producer.start()
        print("[SYSTEM] Engine running. Real-time metrics streaming on ws://localhost:8000")
        print("[SYSTEM] Press Ctrl+C to terminate gracefully.")

    def stop(self) -> None:
        print("\n[SYSTEM] Shutdown signal received. Flushing queues and terminating threads...")
        self.shutdown_event.set()
        
        self.producer.join()
        for consumer in self.consumers:
            consumer.join()
            
        self.alert_processor.join()
        self.ws_reporter.join()
        print("[SYSTEM] All threads terminated. Graceful shutdown complete.")