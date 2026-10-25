"""Maintenance only: embed Standard Ebooks source ZIPs in index.html. No build needed to run Awen.

Download the three named source repositories from github.com/standardebooks as ZIPs,
then run: python tools/refresh_books.py rat.zip wells-war.zip wells-time.zip
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from hashlib import sha256

NS = {"x": "http://www.w3.org/1999/xhtml", "o": "http://www.idpf.org/2007/opf"}
SHELF = [
    ("rat", "The Stainless Steel Rat", "Harry Harrison", "harry-harrison/the-stainless-steel-rat"),
    ("war", "The War of the Worlds", "H. G. Wells", "h-g-wells/the-war-of-the-worlds"),
    ("time", "The Time Machine", "H. G. Wells", "h-g-wells/the-time-machine"),
]


def text(element):
    # Omit inline note reference numbers, retain their tails and all actual prose.
    for parent in element.iter():
        for child in list(parent):
            if "noteref" in child.attrib.get("{http://www.idpf.org/2007/ops}type", ""):
                child.text = ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def extract(path, metadata):
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
        return {"id": book_id, "title": title, "author": author,
                "url": "https://standardebooks.org/ebooks/" + slug,
                "repository": "https://github.com/standardebooks/" + slug.replace("/", "_"),
                "revision": "25 October 2026 · source archive SHA256 " + sha256(Path(path).read_bytes()).hexdigest(),
                "license": archive.read(license_path).decode().strip(),
                "colophon": colophon + endnotes, "chapters": chapters}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    books = [extract(path, meta) for path, meta in zip(sys.argv[1:], SHELF)]
    page = Path(__file__).resolve().parents[1] / "index.html"
    data = json.dumps(books, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    start, end = "<!-- BOOK_DATA_START -->", "<!-- BOOK_DATA_END -->"
    before, rest = page.read_text(encoding="utf-8").split(start)
    _, after = rest.split(end)
    page.write_text(before + start + '\n<script id="books" type="application/json">' + data + "</script>\n" + end + after, encoding="utf-8")
    for b in books:
        print(f'{b["title"]}: {len(b["chapters"])} chapters, {sum(len(c["paragraphs"]) for c in b["chapters"])} paragraphs')
