import os
import sys
import logging
import json

def setup_logger(name: str = "acc"):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)
    
    # JSON formatter for structured logging (production-ready)
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "level": record.levelname,
                "name": record.name,
                "msg": record.getMessage(),
                "time": self.formatTime(record, self.datefmt)
            }
            if record.exc_info:
                log_record["exc_info"] = self.formatException(record.exc_info)
            return json.dumps(log_record)
            
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger

log = setup_logger()
