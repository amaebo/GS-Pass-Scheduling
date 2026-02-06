from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure repo root is on sys.path when running as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.logging import setup_logging
from db import reservations_db as r_db

setup_logging()
logger = logging.getLogger("reservations")

def main() -> int:
    try:
        deleted = r_db.delete_cancelled_expired_passes()
        logger.info("Deleted %s cancelled reservations with expired passes.", deleted)
        return 0
    except Exception:
        logger.exception("Cleanup failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
