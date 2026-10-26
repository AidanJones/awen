"""Maintenance only: embed Standard Ebooks source ZIPs in index.html. No build needed to run Awen.

Download the named source repositories from github.com/standardebooks as ZIPs.
Refresh all: python tools/refresh_books.py rat.zip wells-war.zip wells-time.zip riders.zip
Add/refresh one: python tools/refresh_books.py --add riders riders.zip --retrieved "26 October 2026"
"""
import argparse
from datetime import date
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from hashlib import sha256

NS = {"x": "http://www.w3.org/1999/xhtml", "o": "http://www.idpf.org/2007/opf"}
SHELF = [
    ("rat", "The Stainless Steel Rat", "Harry Harrison", "harry-harrison/the-stainless-steel-rat"),
    ("war", "The War of the Worlds", "H. G. Wells", "h-g-wells/the-war-of-the-worlds"),
    ("time", "The Time Machine", "H. G. Wells", "h-g-wells/the-time-machine"),
    ("riders", "Riders of the Purple Sage", "Zane Grey", "zane-grey/riders-of-the-purple-sage"),
]


def text(element):
    # Omit inline note reference numbers, retain their tails and all actual prose.
    for parent in element.iter():
        for child in list(parent):
            if "noteref" in child.attrib.get("{http://www.idpf.org/2007/ops}type", ""):
                child.text = ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def extract(path, metadata, retrieved=None):
    book_id, title, author, slug = metadata
    with zipfile.ZipFile(path) as archive:
        opf_path = next(n for n in archive.namelist() if n.endswith("/content.opf"))
        base = opf_path.rsplit("/", 1)[0] + "/"
        opf = ET.fromstring(archive.read(opf_path))
        manifest = {n.attrib["id"]: n.attrib["href"] for n in opf.findall("o:manifest/o:item", NS)}
        chapters, colophon, endnotes = [], "", ""
        for item in opf.findall("o:spine/o:itemref", NS):
            href = manifest[item.attrib["idref"]]
            if href.endswith("colophon.xhtml"):
                colophon = text(ET.fromstring(archive.read(base + href)).find("x:body", NS))
            if href.endswith("endnotes.xhtml"):
                endnotes = "\n\nEndnotes: " + text(ET.fromstring(archive.read(base + href)).find("x:body", NS))
            if not re.search(r"/(chapter-[\d-]+|epilogue)\.xhtml$", href):
                continue
            root = ET.fromstring(archive.read(base + href))
            heading = root.find("x:head/x:title", NS)
            name = text(heading) if heading is not None else "Chapter " + str(len(chapters) + 1)
            section = root.find("x:body/x:section", NS)
            if section is not None and section.attrib.get("data-parent", "").startswith("book-"):
                name = "Book " + section.attrib["data-parent"].split("-")[-1] + " · " + name
            heading_paragraphs = {id(p) for h in root.findall(".//x:hgroup", NS) for p in h.findall(".//x:p", NS)}
            paragraphs = [text(p) for p in root.findall(".//x:body//x:p", NS) if id(p) not in heading_paragraphs]
            paragraphs = [p for p in paragraphs if p]
            if paragraphs:
                chapters.append({"id": Path(href).stem, "title": name, "paragraphs": paragraphs})
        license_path = next(n for n in archive.namelist() if n.endswith("/LICENSE.md"))
        assert chapters and all(c["paragraphs"] for c in chapters)
        commit = re.search(r"-([0-9a-f]{40})/", archive.namelist()[0])
        return {"id": book_id, "title": title, "author": author,
                "genre": "Western" if book_id == "riders" else "Science fiction",
                "coverColor": {"rat": "#485b49", "war": "#a4553a", "time": "#334f63", "riders": "#795739"}[book_id],
                "url": "https://standardebooks.org/ebooks/" + slug,
                "repository": "https://github.com/standardebooks/" + slug.replace("/", "_"),
                "revision": (retrieved or date.today().strftime("%d %B %Y")) + " · source archive SHA256 " + sha256(Path(path).read_bytes()).hexdigest() + (" · source commit " + commit[1] if commit else ""),
                "license": archive.read(license_path).decode().strip(),
                "colophon": colophon + endnotes, "chapters": chapters}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="*")
    parser.add_argument("--add", choices=[b[0] for b in SHELF], help="Add/refresh a single edition without changing the others")
    parser.add_argument("--retrieved", help="Human-readable source retrieval date")
    args = parser.parse_args()
    page = Path(__file__).resolve().parents[1] / "index.html"
    html = page.read_text(encoding="utf-8")
    if args.add:
        if len(args.archives) != 1:
            parser.error("--add requires exactly one source archive")
        books = json.loads(re.search(r'<script id="books" type="application/json">([\s\S]*?)</script>', html)[1])
        added = extract(args.archives[0], next(b for b in SHELF if b[0] == args.add), args.retrieved)
        index = next((i for i, b in enumerate(books) if b["id"] == args.add), len(books))
        if index == len(books):
            books.append(added)
        else:
            books[index] = added
    else:
        if len(args.archives) != len(SHELF):
            parser.error(f"provide all {len(SHELF)} archives or use --add")
        books = [extract(path, meta, args.retrieved) for path, meta in zip(args.archives, SHELF)]
    data = json.dumps(books, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    start, end = "<!-- BOOK_DATA_START -->", "<!-- BOOK_DATA_END -->"
    before, rest = html.split(start)
    _, after = rest.split(end)
    page.write_text(before + start + '\n<script id="books" type="application/json">' + data + "</script>\n" + end + after, encoding="utf-8")
    for b in books:
        print(f'{b["title"]}: {len(b["chapters"])} chapters, {sum(len(c["paragraphs"]) for c in b["chapters"])} paragraphs')
