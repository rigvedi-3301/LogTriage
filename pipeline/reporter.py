import asyncio
import json
import queue
import threading
from pipeline.metrics import Metrics
import websockets

class WebSocketMetricsReporter(threading.Thread):
    def __init__(self, log_queue: queue.Queue, alert_queue: queue.Queue, metrics: Metrics, ai_summary_queue: queue.Queue, shutdown_event: threading.Event) -> None:
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.alert_queue = alert_queue
        self.metrics = metrics
        self.ai_summary_queue = ai_summary_queue
        self.shutdown_event = shutdown_event
        self.clients = set()

    async def handler(self, websocket, *args, **kwargs) -> None:
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosedError:
            pass
        finally:
            self.clients.remove(websocket)

    async def broadcaster(self) -> None:
        while not self.shutdown_event.is_set():
            throughput = self.metrics.get_and_reset_throughput()
            stats = self.metrics.get_stats()
            q_depth = self.log_queue.qsize()
            alert_q_depth = self.alert_queue.qsize()
            
            ai_reports = []
            while not self.ai_summary_queue.empty():
                try:
                    ai_reports.append(self.ai_summary_queue.get_nowait())
                except queue.Empty:
                    break
                    
            ai_analysis = "\n\n---\n\n".join(ai_reports) if ai_reports else None
            
            print(f"[METRICS] Throughput: {throughput:6d} logs/sec | "
                  f"Queue Depth: {q_depth:5d} | "
                  f"Alerts Queue: {alert_q_depth:4d} | "
                  f"Total Alerts: {stats['alerts']:6d} | "
                  f"Total Drops: {stats['dropped']:6d}")
                  
            if self.clients:
                payload = json.dumps({
                    "throughput": throughput,
                    "queue_depth": q_depth,
                    "alert_queue_depth": alert_q_depth,
                    "total_alerts": stats["alerts"],
                    "total_drops": stats["dropped"],
                    "ai_analysis": ai_analysis
                })
                websockets.broadcast(self.clients, payload)
                
            await asyncio.sleep(1.0)

    async def main_server(self) -> None:
        async with websockets.serve(self.handler, "localhost", 8000):
            broadcast_task = asyncio.create_task(self.broadcaster())
            while not self.shutdown_event.is_set():
                await asyncio.sleep(0.5)
            broadcast_task.cancel()

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.main_server())
        except asyncio.CancelledError:
            pass
        finally:
            loop.close()