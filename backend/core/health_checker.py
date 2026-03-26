import logging
import requests

logger = logging.getLogger(__name__)


def check_health(port: int = 8081):
    """检查推理服务是否正常"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False
