from pathlib import Path

from fastapi.templating import Jinja2Templates


APP_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

templates = Jinja2Templates(directory=TEMPLATE_DIR)


def styles_version() -> int:
    return (STATIC_DIR / "styles.css").stat().st_mtime_ns


templates.env.globals["styles_version"] = styles_version
