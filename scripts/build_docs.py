"""Собирает статическую копию сайта для GitHub Pages.

GitHub Pages умеет отдавать папку /docs из ветки main. Исходники интерфейса
лежат в web/, поэтому перед публикацией достаточно выполнить:

    python scripts/build_docs.py

Скрипт копирует web/ в docs/ и добавляет .nojekyll, чтобы GitHub не пытался
обрабатывать файлы через Jekyll. Ссылки в HTML относительные, поэтому сайт
работает и в корне домена, и в подкаталоге /<repo>/.
"""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web"
DST = ROOT / "docs"


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"web/ not found: {SRC}")

    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    (DST / ".nojekyll").write_text("", encoding="utf-8")

    pages = sorted(p.name for p in DST.glob("*.html"))
    assets = sorted(p.name for p in (DST / "assets").iterdir())
    print(f"docs/: {', '.join(pages)}")
    print(f"assets: {', '.join(assets)}")


if __name__ == "__main__":
    main()
