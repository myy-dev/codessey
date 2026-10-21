import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi import Request

from app.main import app
from app.templating import templates


class StylesheetVersionTestCase(unittest.TestCase):
    def test_changed_stylesheet_gets_a_new_url_without_restarting(self) -> None:
        request = Request({
            "type": "http", "method": "GET", "path": "/", "root_path": "",
            "scheme": "http", "server": ("testserver", 80), "headers": [], "app": app,
        })

        def stylesheet_url() -> str:
            response = templates.TemplateResponse(request=request, name="home.html")
            match = re.search(r'<link rel="stylesheet" href="([^"]+)"', response.body.decode())
            self.assertIsNotNone(match)
            return match[1]

        with TemporaryDirectory() as directory, patch("app.templating.STATIC_DIR", Path(directory)):
            stylesheet = Path(directory) / "styles.css"
            stylesheet.write_text("/* first version */")
            os.utime(stylesheet, ns=(1_000_000_000, 1_000_000_000))
            before = stylesheet_url()
            stylesheet.write_text("/* changed version */")
            os.utime(stylesheet, ns=(2_000_000_000, 2_000_000_000))
            after = stylesheet_url()

        self.assertNotEqual(before, after)
        self.assertEqual(before.split("?")[0], after.split("?")[0])
