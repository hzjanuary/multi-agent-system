"""Validate configuration safely without printing secrets or contacting models."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=".maos/.env")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    try:
        from app.config import Settings

        settings = Settings(_env_file=args.env_file)
        settings.llm_settings.require_provider_configuration()
    except Exception:
        errors.append(
            "configuration_invalid: check required database/JWT/provider/model settings"
        )
    result = {"status": "invalid" if errors else "valid", "errors": errors}
    if args.json:
        print(json.dumps(result))
    else:
        print(result["status"])
        for error in errors:
            print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
