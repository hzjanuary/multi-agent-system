"""Environment validation reports bounded safe errors."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ops import validate_environment


class ValidateEnvironmentTests(unittest.TestCase):
    def test_invalid_secrets_are_never_echoed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("DATABASE_URL=secret-value\nJWT_SECRET_KEY=secret-value\n")
            output = io.StringIO()
            with patch.object(
                sys, "argv", ["validate", "--env-file", str(path), "--json"]
            ), contextlib.redirect_stdout(output):
                code = validate_environment.main()
            self.assertEqual(code, 1)
            self.assertNotIn("secret-value", output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["status"], "invalid")
