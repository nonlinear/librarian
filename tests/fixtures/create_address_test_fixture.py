#!/usr/bin/env python3
"""Create the address-test.epub fixture for fitness function address tests.

Structure:
  address-test.epub/
  ├── mimetype
  ├── META-INF/
  │   └── container.xml
  └── OPS/
      ├── content.opf
      ├── toc.ncx
      └── chapter1.xhtml
"""

import io
import os
import zipfile

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "address-test.epub")


def build_epub() -> bytes:
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. mimetype — MUST be first, uncompressed, no extra fields
        info = zipfile.ZipInfo("mimetype")
        info.external_attr = 0o644 << 16
        zf.writestr(info, "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/container.xml
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
            '  <rootfiles>\n'
            '    <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>\n'
            '  </rootfiles>\n'
            '</container>\n',
        )

        # 3. OPS/content.opf
        zf.writestr(
            "OPS/content.opf",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">\n'
            '  <metadata>\n'
            '    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Address Test Fixture</dc:title>\n'
            '    <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">en</dc:language>\n'
            '    <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/" id="bookid">urn:uuid:address-test-fixture</dc:identifier>\n'
            '  </metadata>\n'
            '  <manifest>\n'
            '    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>\n'
            '    <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n'
            '  </manifest>\n'
            '  <spine toc="toc">\n'
            '    <itemref idref="chapter1"/>\n'
            '  </spine>\n'
            '</package>\n',
        )

        # 4. OPS/toc.ncx
        zf.writestr(
            "OPS/toc.ncx",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\n'
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
            '  <head>\n'
            '    <meta name="dtb:uid" content="urn:uuid:address-test-fixture"/>\n'
            '  </head>\n'
            '  <docTitle>\n'
            '    <text>Address Test Fixture</text>\n'
            '  </docTitle>\n'
            '  <navMap>\n'
            '    <navPoint id="navpoint-1" playOrder="1">\n'
            '      <navLabel>\n'
            '        <text>Chapter 1</text>\n'
            '      </navLabel>\n'
            '      <content src="chapter1.xhtml"/>\n'
            '    </navPoint>\n'
            '  </navMap>\n'
            '</ncx>\n',
        )

        # 5. OPS/chapter1.xhtml — 3 paragraphs
        zf.writestr(
            "OPS/chapter1.xhtml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml">\n'
            '<head>\n'
            '  <title>Chapter 1</title>\n'
            '</head>\n'
            '<body>\n'
            '  <p>This is the first paragraph of the address test fixture.</p>\n'
            '  <p>This is the second paragraph, used for mid-document address resolution.</p>\n'
            '  <p>This is the third and final paragraph, at the end of the document.</p>\n'
            '</body>\n'
            '</html>\n',
        )

    return buf.getvalue()


def main():
    data = build_epub()
    with open(OUTPUT_PATH, "wb") as f:
        f.write(data)
    print(f"✓ Created {OUTPUT_PATH} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
