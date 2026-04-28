#!/usr/bin/env python3
"""
Import items from a local directory.

Each subdirectory of PATH becomes one Item (nombre = directory name).
Image files inside become photos attached to that item.

Usage:
    uv run scripts/import_unsorted.py PATH --email EMAIL [--password PASS] [--url BASE_URL]
"""

import argparse
import getpass
import re
import sys
from pathlib import Path

import requests

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _csrf(session):
    return session.cookies.get("csrftoken", "")


def login(session, base, email, password):
    session.get(f"{base}/login/")
    resp = session.post(
        f"{base}/login/",
        data={"username": email, "password": password, "csrfmiddlewaretoken": _csrf(session)},
        allow_redirects=False,
    )
    return resp.status_code == 302


def create_item(session, base, nombre):
    resp = session.post(
        f"{base}/items/nueva/",
        data={"nombre": nombre, "csrfmiddlewaretoken": _csrf(session)},
        allow_redirects=False,
    )
    if resp.status_code != 302:
        return None
    m = re.search(r"/items/(\d+)/", resp.headers.get("Location", ""))
    return int(m.group(1)) if m else None


def upload_photo(session, base, item_pk, img_path):
    with open(img_path, "rb") as f:
        resp = session.post(
            f"{base}/items/{item_pk}/fotos/",
            data={"csrfmiddlewaretoken": _csrf(session)},
            files={"image": (img_path.name, f)},
            allow_redirects=False,
        )
    return resp.status_code == 302


def main():
    parser = argparse.ArgumentParser(description="Import items from a local directory into Museoman")
    parser.add_argument("path", help="Directory: each subdirectory = one item")
    parser.add_argument("--url", default="http://localhost:8000", metavar="URL")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", metavar="PASS", help="Prompted if omitted")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"Error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    subdirs = sorted(p for p in root.iterdir() if p.is_dir())
    if not subdirs:
        print("No subdirectories found.", file=sys.stderr)
        sys.exit(1)

    password = args.password or getpass.getpass(f"Password for {args.email}: ")
    base = args.url.rstrip("/")

    session = requests.Session()
    if not login(session, base, args.email, password):
        print("Login failed.", file=sys.stderr)
        sys.exit(1)

    created_items = created_photos = errors = 0

    for subdir in subdirs:
        nombre = subdir.name
        item_pk = create_item(session, base, nombre)
        if item_pk is None:
            print(f"  [{nombre}] ERROR: could not create item", file=sys.stderr)
            errors += 1
            continue
        created_items += 1

        image_files = sorted(f for f in subdir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS)
        for img_path in image_files:
            if upload_photo(session, base, item_pk, img_path):
                created_photos += 1
            else:
                print(f"    [{img_path.name}] ERROR: upload failed", file=sys.stderr)
                errors += 1

        print(f"  {nombre} (id={item_pk}): {len(image_files)} foto(s)")

    print(f"\nDone: {created_items} items, {created_photos} photos.")
    if errors:
        print(f"{errors} error(s) above.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
