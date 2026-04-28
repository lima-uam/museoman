#!/usr/bin/env python3
"""
Import vitrinas, slotted items and photos from a directory tree.

Expected structure:
    PATH/<vitrina name>/<slot>/<photos...>

Each top-level directory becomes a new Vitrina.
Each child directory becomes an Item named "Sin clasificar N" assigned to that
Vitrina. If the child directory name is a single hex character (0-9 or A-F,
case-insensitive) it is used as the item's slot; otherwise the slot is left blank.

Usage:
    uv run scripts/import_sorted.py PATH --email EMAIL [--password PASS] [--url BASE_URL]
"""

import argparse
import getpass
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import requests

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@dataclass
class ItemPlan:
    nombre: str
    vitrina_nombre: str
    vitrina_pk: int | None
    slot: str
    photos: list[Path] = field(default_factory=list)
    pk: int | None = None


def _csrf(session):
    return session.cookies.get("csrftoken", "")


def login(session, base, email, password):
    session.get(f"{base}/login/")
    resp = session.post(
        f"{base}/login/",
        data={
            "username": email,
            "password": password,
            "csrfmiddlewaretoken": _csrf(session),
        },
        allow_redirects=False,
    )
    return resp.status_code == 302


def _vitrina_pks(session, base):
    resp = session.get(f"{base}/catalog/vitrinas/")
    return set(map(int, re.findall(r"/catalog/vitrinas/(\d+)/editar/", resp.text)))


def create_vitrina(session, base, nombre):
    before = _vitrina_pks(session, base)
    resp = session.post(
        f"{base}/catalog/vitrinas/nueva/",
        data={"nombre": nombre, "url": "", "csrfmiddlewaretoken": _csrf(session)},
        allow_redirects=False,
    )
    if resp.status_code != 302:
        return None
    after = _vitrina_pks(session, base)
    new = after - before
    if len(new) != 1:
        return None
    return new.pop()


def create_item(session, base, nombre, vitrina_pk, slot):
    resp = session.post(
        f"{base}/items/nueva/",
        data={
            "nombre": nombre,
            "vitrina": vitrina_pk,
            "vitrina_slot": slot,
            "url": "",
            "observaciones": "",
            "csrfmiddlewaretoken": _csrf(session),
        },
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


def build_plan(root):
    items = []
    counter = 1
    for vitrina_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        slot_dirs = sorted(p for p in vitrina_dir.iterdir() if p.is_dir())
        for slot_dir in slot_dirs:
            slot = slot_dir.name.upper()
            if not re.fullmatch(r"[0-9A-F]", slot):
                slot = ""
            photos = sorted(
                f
                for f in slot_dir.iterdir()
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            )
            items.append(
                ItemPlan(
                    nombre=f"Sin clasificar {counter}",
                    vitrina_nombre=vitrina_dir.name,
                    vitrina_pk=None,
                    slot=slot,
                    photos=photos,
                )
            )
            counter += 1
    return items


def main():
    parser = argparse.ArgumentParser(
        description="Import vitrinas and slotted items from a directory tree"
    )
    parser.add_argument("path", help="Root directory: each subdir = one vitrina")
    parser.add_argument("--url", default="http://localhost:8000", metavar="URL")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", metavar="PASS", help="Prompted if omitted")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"Error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    plan = build_plan(root)
    if not plan:
        print("No items found (no slot subdirectories).", file=sys.stderr)
        sys.exit(1)

    vitrina_names = list(dict.fromkeys(item.vitrina_nombre for item in plan))
    print(
        f"Plan: {len(vitrina_names)} vitrina(s), {len(plan)} item(s), {sum(len(i.photos) for i in plan)} photo(s)."
    )

    password = args.password or getpass.getpass(f"Password for {args.email}: ")
    base = args.url.rstrip("/")

    session = requests.Session()
    if not login(session, base, args.email, password):
        print("Login failed.", file=sys.stderr)
        sys.exit(1)

    # Create vitrinas
    vitrina_pks: dict[str, int] = {}
    for nombre in vitrina_names:
        pk = create_vitrina(session, base, nombre)
        if pk is None:
            print(f"ERROR: could not create vitrina '{nombre}'.", file=sys.stderr)
            sys.exit(1)
        vitrina_pks[nombre] = pk
        print(f"  Vitrina '{nombre}' -> id={pk}")

    # Create items
    for item in plan:
        item.vitrina_pk = vitrina_pks[item.vitrina_nombre]
        pk = create_item(session, base, item.nombre, item.vitrina_pk, item.slot)
        if pk is None:
            print(
                f"ERROR: could not create item '{item.nombre}' (vitrina={item.vitrina_pk} slot='{item.slot}').",
                file=sys.stderr,
            )
            sys.exit(1)
        item.pk = pk
        slot_label = f" slot={item.slot}" if item.slot else ""
        print(f"  {item.nombre} -> id={pk}{slot_label} ({len(item.photos)} foto(s))")

    # Upload photos (print remaining on first failure)
    pending = [(item.pk, photo) for item in plan for photo in item.photos]
    uploaded = 0
    for i, (item_pk, photo) in enumerate(pending):
        if not upload_photo(session, base, item_pk, photo):
            print(f"ERROR: upload failed: {photo} -> item {item_pk}", file=sys.stderr)
            remaining = pending[i:]
            print("Pendiente tras fallo:", file=sys.stderr)
            for rpk, rpath in remaining:
                print(f"{rpk}\t{rpath}", file=sys.stderr)
            sys.exit(1)
        uploaded += 1

    print(
        f"\nDone: {len(vitrina_names)} vitrinas, {len(plan)} items, {uploaded} photos."
    )


if __name__ == "__main__":
    main()
