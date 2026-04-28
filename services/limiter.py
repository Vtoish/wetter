# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter: Limiter = Limiter(key_func=get_remote_address, default_limits=[])
