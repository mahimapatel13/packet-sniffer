import logging
import sys

# Configure a unified format for our logs
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set levels for third party logs if necessary
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("scapy.runtime").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger("traffic-analyzer")
