#!/usr/bin/env python3
"""Regenerate clean EPUB for Ihde from the Shelfmark EPUB XML pages."""
import zipfile, io, os, sys
from bs4 import BeautifulSoup

# Boundary: resolve corpus root via config (engine knows no instance paths)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_config
_cfg = get_config()
_BASE = str(_cfg.corpus_path).rstrip("/") + "/"

path = f'{_BASE}no-indexing/ihde-technology-and-the-lifeworld.epub'
if not os.path.exists(path):
    path = f'{_BASE}ihde-technology-and-the-lifeworld.epub'
    if not os.path.exists(path):
        print("Ihde EPUB not found")
        sys.exit(1)

with zipfile.ZipFile(path) as z:
    all_text = []
    xml_pages = sorted([n for n in z.namelist() if n.startswith('content/page_') and n.endswith('.xml')])
    if not xml_pages:
        print("No XML pages found - checking all files")
        for n in z.namelist()[:20]:
            print(f"  {n}")
        sys.exit(1)
    for n in xml_pages:
        soup = BeautifulSoup(z.read(n), 'xml')
        t = soup.get_text(separator='\n', strip=True)
        if t:
            all_text.append(t)
    full = '\n\n'.join(all_text)
    print(f"Extracted {len(full)} chars from {len(xml_pages)} pages")

buf = io.BytesIO()
chunk_parts = [full[i:i+50000] for i in range(0, len(full), 50000)]

with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype', 'application/epub+zip')
    z.writestr('META-INF/container.xml', '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
    z.writestr('OEBPS/style.css', 'body { font-family: serif; } p { text-indent: 1em; margin: 0.3em 0; }')
    
    for i, chunk in enumerate(chunk_parts):
        fname = f'chap{i:02d}.xhtml'
        paragraphs = chunk.split('\n\n')
        html_body = '\n'.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
        html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter {i+1}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><h1>Chapter {i+1}</h1>{html_body}</body></html>'''
        z.writestr(f'OEBPS/{fname}', html.encode('utf-8'))
    
    # OPF
    mf = '\n'.join(f'<item id="chap{i:02d}" href="chap{i:02d}.xhtml" media-type="application/xhtml+xml"/>' for i in range(len(chunk_parts)))
    sf = '\n'.join(f'<itemref idref="chap{i:02d}"/>' for i in range(len(chunk_parts)))
    nf = '\n'.join(f'<li><a href="chap{i:02d}.xhtml">Chapter {i+1}</a></li>' for i in range(len(chunk_parts)))
    
    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/" unique-identifier="bookid" version="3.0">
<metadata>
<dc:identifier id="bookid">urn:uuid:ihde-1990-clean</dc:identifier>
<dc:title>Technology and the Lifeworld: From Garden to Earth</dc:title>
<dc:creator>Don Ihde</dc:creator>
<dc:language>en</dc:language>
<meta property="dcterms:modified">2026-07-12T00:00:00Z</meta>
</metadata>
<manifest>
<item id="css" href="style.css" media-type="text/css"/>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
{mf}
</manifest>
<spine>
{sf}
</spine>
</package>'''
    z.writestr('OEBPS/content.opf', opf.encode('utf-8'))
    
    nav = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body><nav epub:type="toc"><h1>Table of Contents</h1><ol>{nf}</ol></nav></body></html>'''
    z.writestr('OEBPS/nav.xhtml', nav.encode('utf-8'))

# Write to _papers
out = f'{_BASE}_papers/ihde-technology-and-the-lifeworld.epub'
with open(out, 'wb') as f:
    f.write(buf.getvalue())
print(f"Created {out}: {os.path.getsize(out)} bytes")
