from flask_limiter import Limiter  # type: ignore[import-untyped]
from flask_limiter.util import get_remote_address  # type: ignore[import-untyped]

limiter: Limiter = Limiter(key_func=get_remote_address, default_limits=[])
