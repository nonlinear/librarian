#!/usr/bin/env python3
"""Build a minimal valid EPUB 2 fixture for address testing."""

import zipfile
import os
from datetime import datetime

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "address-test.epub")

UUID = "urn:uuid:12345678-1234-5678-1234-567812345678"

# mimetype — plain, no compression, no extra fields
mimetype_data = b"application/epub+zip"

# container.xml — points to content.opf
container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

# content.opf
content_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="BookId">{uuid}</dc:identifier>
    <dc:title>Address Test Fixture</dc:title>
    <dc:creator>Librarian</dc:creator>
    <dc:language>en</dc:language>
    <dc:date>{date}</dc:date>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>
""".format(uuid=UUID, date=datetime.utcnow().strftime("%Y-%m-%d"))

# toc.ncx
toc_ncx = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{uuid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>Address Test Fixture</text>
  </docTitle>
  <navMap>
    <navPoint id="navpoint-1" playOrder="1">
      <navLabel>
        <text>Chapter 1</text>
      </navLabel>
      <content src="chapter1.xhtml"/>
    </navPoint>
  </navMap>
</ncx>
""".format(uuid=UUID)

# chapter1.xhtml
chapter1_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Chapter 1</title>
</head>
<body>
  <p>Paragraph 1 of address test fixture. This EPUB is used to validate that the address extraction pipeline can correctly parse and extract textual content from a standard EPUB file structure. The fixture exercises chapter detection, paragraph splitting, and whitespace normalization.</p>
  <p>Paragraph 2 continues here. Key verification points include proper XML namespace handling, correct spine traversal through the OPF manifest, and accurate reconstruction of the original paragraph order as authored in the XHTML source document.</p>
  <p>Paragraph 3 ends the test. Additional edge cases such as empty paragraphs, nested elements, and mixed inline formatting are covered by separate fixtures in this same directory. This concludes the address test fixture.</p>
</body>
</html>
"""

# Build EPUB
with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
    # mimetype: STORED, no compression, added first
    zf.writestr("mimetype", mimetype_data, compress_type=zipfile.ZIP_STORED)
    # The rest with DEFLATED
    zf.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
    zf.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
    zf.writestr("OEBPS/toc.ncx", toc_ncx, compress_type=zipfile.ZIP_DEFLATED)
    zf.writestr("OEBPS/chapter1.xhtml", chapter1_xhtml, compress_type=zipfile.ZIP_DEFLATED)

# Validate
import xml.etree.ElementTree as ET

size = os.path.getsize(OUTPUT)
errors = []

with zipfile.ZipFile(OUTPUT, "r") as zf:
    names = zf.namelist()

    # Check mimetype is first entry
    if names[0] != "mimetype":
        errors.append("mimetype is not the first entry")

    # Check mimetype is STORED
    info = zf.getinfo("mimetype")
    if info.compress_type != zipfile.ZIP_STORED:
        errors.append("mimetype is not STORED (compress_type=%d)" % info.compress_type)

    # Check mimetype content
    if zf.read("mimetype") != b"application/epub+zip":
        errors.append("mimetype content mismatch")

    # Parse container.xml
    try:
        container = ET.fromstring(zf.read("META-INF/container.xml"))
        ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
        rootfile = container.find(".//c:rootfile", ns)
        opf_path = rootfile.get("full-path")
        if opf_path != "OEBPS/content.opf":
            errors.append("container.xml rootfile path mismatch: %s" % opf_path)
    except Exception as e:
        errors.append("container.xml parse error: %s" % e)

    # Parse content.opf
    try:
        opf = ET.fromstring(zf.read("OEBPS/content.opf"))
        dc = {"dc": "http://purl.org/dc/elements/1.1/"}
        titles = opf.findall(".//dc:title", dc)
        creators = opf.findall(".//dc:creator", dc)
        if not titles or titles[0].text != "Address Test Fixture":
            errors.append("title mismatch: %s" % (titles[0].text if titles else "missing"))
        if not creators or creators[0].text != "Librarian":
            errors.append("creator mismatch: %s" % (creators[0].text if creators else "missing"))
    except Exception as e:
        errors.append("content.opf parse error: %s" % e)

    # Check chapter content
    try:
        chap = ET.fromstring(zf.read("OEBPS/chapter1.xhtml"))
        paras = chap.findall(".//{http://www.w3.org/1999/xhtml}p")
        para_texts = [''.join(p.itertext()) for p in paras]
        expected = [
            "Paragraph 1 of address test fixture. This EPUB is used to validate that the address extraction pipeline can correctly parse and extract textual content from a standard EPUB file structure. The fixture exercises chapter detection, paragraph splitting, and whitespace normalization.",
            "Paragraph 2 continues here. Key verification points include proper XML namespace handling, correct spine traversal through the OPF manifest, and accurate reconstruction of the original paragraph order as authored in the XHTML source document.",
            "Paragraph 3 ends the test. Additional edge cases such as empty paragraphs, nested elements, and mixed inline formatting are covered by separate fixtures in this same directory. This concludes the address test fixture.",
        ]
        if para_texts != expected:
            errors.append("chapter paragraphs mismatch: %s" % para_texts)
    except Exception as e:
        errors.append("chapter1.xhtml parse error: %s" % e)

print("=== (a) Script ===")
print(__file__)
print()
print("=== (b) Metadata ===")
print("Title:    Address Test Fixture")
print("Creator:  Librarian")
print("Identifier:", UUID)
print("Language: en")
print()
print("=== (c) File size ===")
print("Size: %d bytes (%.1f KB)" % (size, size / 1024))
print()
print("=== (d) Validation ===")
print("Files in EPUB:", names)
print("Errors:", errors if errors else "None — EPUB is valid!")
