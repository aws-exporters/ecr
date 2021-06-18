import os
import logging
import time
import sys
import signal
from typing import List
from pythonjsonlogger import jsonlogger
from prometheus_client import start_http_server, Gauge
from prometheus_client.core import REGISTRY
from collector import ECRMetricsCollector


def config_from_env():
    config = {}
    config['port'] = int(os.getenv('APP_PORT', 9000))
    config['host'] = os.getenv('APP_HOST', '0.0.0.0')
    config['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
    config['registry_id'] = os.getenv('ECR_REGISTRY_ID', None)
    config['refresh_interval'] = int(os.getenv('CACHE_REFRESH_INTERVAL', 600))
    
    return config

def setup_logging(log_level):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    
def main(config):
    shutdown = False

    # Setup logging
    setup_logging(config['log_level'])
    logger = logging.getLogger()
    
    # Register signal handler
    def _on_sigterm(signal, frame):
        logging.getLogger().warning('exporter is shutting down')
        nonlocal shutdown
        shutdown = True

    signal.signal(signal.SIGINT, _on_sigterm)
    signal.signal(signal.SIGTERM, _on_sigterm)

    # Register our custom collector
    logger.warning('collecting initial metrics')
    ecr_collector = ECRMetricsCollector(config['registry_id'])
    REGISTRY.register(ecr_collector)

    # Set the up metric value, which will be steady to 1 for the entire app lifecycle
    upMetric = Gauge(
        'ecr_repository_exporter_up',
        'always 1 - can by used to check if it\'s running')

    upMetric.set(1)

    # Start server
    start_http_server(config['port'], config['host'])
    logger.warning(f"exporter listening on http://{config['host']}:{config['port']}/")

    logger.info(f"caches will be refreshed every {config['refresh_interval']} seconds")
    loop_count = 0
    while not shutdown:
        loop_count += 1
        time.sleep(1)
        
        if loop_count >= config['refresh_interval']:
            ecr_collector.refresh_caches()
            loop_count = 0
            
    logger.info('exporter has shutdown')


def run():
    main(config_from_env())

if __name__ == '__main__':
    run()