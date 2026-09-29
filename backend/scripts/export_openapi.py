"""Write the API's OpenAPI schema to a file.

The frontend generates its TypeScript types from this file (`npm run gen:api` in
frontend/), so the two sides can never silently drift apart.

    uv run python -m scripts.export_openapi ../frontend/openapi.json
"""

import json
import sys
from pathlib import Path

from app.main import app


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m scripts.export_openapi <output.json>")
        return 2
    Path(args[0]).write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
