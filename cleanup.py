import os
import shutil
import time
from logging_config import logger

STORAGE_DIR = "storage"
TTL_SECONDS = 3600


def cleanup_old_sessions():
    if not os.path.exists(STORAGE_DIR):
        return

    current_time = time.time()

    for session_id in os.listdir(STORAGE_DIR):
        session_path = os.path.join(STORAGE_DIR, session_id)

        if not os.path.isdir(session_path):
            continue

        try:
            mtime = os.path.getmtime(session_path)
            if current_time - mtime > TTL_SECONDS:
                shutil.rmtree(session_path)
                logger.info(f"Удалена устаревшая сессия: {session_id}")
        except Exception as e:
            logger.error(f"Ошибка при удалении сессии {session_id}: {e}")


def cleanup_archive(archive_path: str):
    try:
        if os.path.exists(archive_path):
            os.remove(archive_path)
            logger.info(f"Удален архив: {archive_path}")
    except Exception as e:
        logger.error(f"Ошибка при удалении архива {archive_path}: {e}")
