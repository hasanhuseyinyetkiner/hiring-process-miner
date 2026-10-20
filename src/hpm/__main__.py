import logging
import sys

import uvicorn

from hpm.config import assert_bind_allowed, get_settings
from hpm.errors import BindRefused


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    settings = get_settings()
    try:
        assert_bind_allowed(settings.host, settings.allow_network_bind)
    except BindRefused as exc:
        raise SystemExit(str(exc)) from exc
    uvicorn.run(
        "hpm.main:app",
        host=settings.host,
        port=settings.port,
        factory=False,
    )


if __name__ == "__main__":
    sys.exit(main())
