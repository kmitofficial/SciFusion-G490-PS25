"""AutoAD backend FastAPI application package."""

from __future__ import annotations

import sys
from pathlib import Path

try:  # pragma: no cover - best-effort dotenv support
	from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
	load_dotenv = None  # type: ignore[assignment]


if load_dotenv is not None:
	# Load environment variables from repos `.env` so background workers share CLI setup.
	env_path = Path(__file__).resolve().parents[2] / ".env"
	if env_path.exists():
		load_dotenv(dotenv_path=env_path, override=False)


# Ensure the backend root (which houses dolphin_utils and other modules)
# is importable when the FastAPI app is launched via ``uvicorn --app-dir server``.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:  # pragma: no cover - defensive path wiring
	sys.path.append(str(_BACKEND_ROOT))

# Surface the resolved backend root for other modules if needed.
__all__ = ["_BACKEND_ROOT"]
