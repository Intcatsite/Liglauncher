"""Entry point: ``python -m liglauncher`` or installed ``liglauncher`` script."""
from __future__ import annotations

import logging
import sys
import traceback

from .log import setup_logging
from .paths import logs_dir


def main() -> int:
    setup_logging(logs_dir())
    log = logging.getLogger("liglauncher")
    try:
        # Imported lazily so that --help / packaging tools don't require Tk at import time.
        from .ui.app import run

        run()
        return 0
    except Exception:  # noqa: BLE001
        log.error("Fatal error:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
