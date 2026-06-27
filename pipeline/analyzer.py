import os
import queue
import threading
import time
import requests
from collections import defaultdict, deque
from typing import Dict, Any, DefaultDict
from google import genai
from google.genai import types

class AlertWindowProcessor(threading.Thread):
    def __init__(self, alert_queue: queue.Queue, ai_summary_queue: queue.Queue, shutdown_event: threading.Event) -> None:
        super().__init__(daemon=True)
        self.alert_queue = alert_queue
        self.ai_summary_queue = ai_summary_queue
        self.shutdown_event = shutdown_event
        self.window_duration = 5.0
        self.last_flush_time = time.time()
        self.anomaly_threshold = 50
        
        self.webhook_url = os.environ.get("WEBHOOK_URL", "")
        from concurrent.futures import ThreadPoolExecutor
        self.ai_worker_pool = ThreadPoolExecutor(max_workers=3)
        self.client = genai.Client()
        self.model_name = "gemini-2.5-flash"
        
        self.system_instruction = (
            "You are an on-call Google Site Reliability Engineer (SRE). "
            "Review the aggregated log anomaly report from the last 5 seconds and provide a concise, "
            "3-bullet-point markdown incident summary detailing the likely root cause and critical blast radius. "
            "Keep it brutally direct."
        )
        self.window_data = self._create_empty_window()

    def _create_empty_window(self) -> DefaultDict[str, Dict[str, Any]]:
        return defaultdict(lambda: {"ERROR": 0, "CRITICAL": 0, "samples": deque(maxlen=3)})

    def _flush_window(self) -> None:
        if not self.window_data:
            self.last_flush_time = time.time()
            return
            
        total_anomalies = sum(stats["ERROR"] + stats["CRITICAL"] for stats in self.window_data.values())
        
        if total_anomalies < self.anomaly_threshold:
            print(f"[AI-SILENT] System healthy ({total_anomalies} errors < {self.anomaly_threshold}). Skipping LLM dispatch.")
            self.window_data = self._create_empty_window()
            self.last_flush_time = time.time()
            return
            
        report_lines = []
        for service, stats in self.window_data.items():
            err_count = stats["ERROR"]
            crit_count = stats["CRITICAL"]
            samples_joined = " | ".join(stats["samples"])
            report_lines.append(
                f"Service {service} experienced {err_count} ERRORs and {crit_count} CRITICAL errors. Samples: [{samples_joined}]"
            )
            
        report_payload = "\n".join(report_lines)
        self.window_data = self._create_empty_window()
        self.last_flush_time = time.time()
        
        self.ai_worker_pool.submit(self._analyze_anomalies_async, report_payload)

    def _analyze_anomalies_async(self, report_payload: str) -> None:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=report_payload,
                config=types.GenerateContentConfig(system_instruction=self.system_instruction)
            )
            summary = response.text.strip() if response.text else "No response generated."
            print("\n" + "="*60 + f"\n[AI SRE INCIDENT SUMMARY]\n{summary}\n" + "="*60 + "\n")
            
            self.ai_summary_queue.put_nowait(summary)
            
            if self.webhook_url:
                requests.post(self.webhook_url, json={"text": summary, "content": summary}, timeout=5.0)
        except Exception as e:
            print(f"\n[AI SRE ERROR] Failed to fetch analysis from Gemini API: {e}\n")

    def run(self) -> None:
        while not self.shutdown_event.is_set() or not self.alert_queue.empty():
            try:
                alert = self.alert_queue.get(timeout=0.2)
            except queue.Empty:
                pass
            else:
                service = alert.get("service", "unknown")
                level = alert.get("level", "ERROR")
                message = alert.get("message", "")
                
                if level in ("ERROR", "CRITICAL"):
                    self.window_data[service][level] += 1
                    self.window_data[service]["samples"].append(message)
                self.alert_queue.task_done()
                
            if time.time() - self.last_flush_time >= self.window_duration:
                self._flush_window()
                
        self._flush_window()
        self.ai_worker_pool.shutdown(wait=True)