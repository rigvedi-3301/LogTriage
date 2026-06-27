import time
from pipeline.engine import LogParsingEngine

if __name__ == "__main__":
    engine = LogParsingEngine()
    engine.start()
    
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        engine.stop()