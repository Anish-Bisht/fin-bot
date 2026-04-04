import logging
import sys
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
        }
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logger(name="finbot"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console Handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
