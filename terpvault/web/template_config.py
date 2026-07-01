from pathlib import Path
from jinja2 import Environment, FileSystemLoader


_template_dir = Path(__file__).resolve().parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_template_dir)), enable_async=False)


def render_string(name: str, **context) -> str:
    template = _env.get_template(name)
    return template.render(**context)
