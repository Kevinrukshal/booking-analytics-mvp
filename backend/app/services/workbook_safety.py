"""Bound compressed spreadsheets before pandas/openpyxl materialize cells."""
from io import BytesIO
from zipfile import BadZipFile, ZipFile
from defusedxml.ElementTree import iterparse
from app.core.config import settings


def validate_workbook(content: bytes) -> None:
    try:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 1000 or sum(e.file_size for e in entries) > settings.max_expanded_mb * 1024 * 1024:
                raise ValueError("Workbook expanded size exceeds the safety limit.")
            sheets = [e for e in entries if e.filename.startswith("xl/worksheets/") and e.filename.endswith(".xml")]
            if not sheets or len(sheets) > settings.max_workbook_sheets:
                raise ValueError("Workbook sheet count exceeds the safety limit.")
            if any("vbaproject" in e.filename.lower() or "externallinks/" in e.filename.lower() or e.flag_bits & 1 for e in entries):
                raise ValueError("Macros, external workbook links and encrypted entries are not supported.")
            rows = cells = 0
            for entry in sheets:
                with archive.open(entry) as xml:
                    for _, element in iterparse(xml, events=("end",)):
                        tag = element.tag.rsplit("}", 1)[-1]
                        if tag == "row":
                            rows += 1
                            if rows > settings.max_workbook_rows or int(element.get("r", "0")) > settings.max_workbook_rows:
                                raise ValueError("Workbook row count exceeds the safety limit.")
                        elif tag == "c":
                            cells += 1
                            ref = element.get("r", "")
                            letters = "".join(c for c in ref if c.isalpha())
                            column = 0
                            for letter in letters.upper():
                                column = column * 26 + ord(letter) - 64
                            if cells > settings.max_workbook_cells or column > 256:
                                raise ValueError("Workbook cell count or column count exceeds the safety limit.")
                        element.clear()
    except ValueError:
        raise
    except Exception:
        raise ValueError("Invalid or unsupported workbook.") from None
