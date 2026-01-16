import html
import io
import re
import sys

from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional
from xml.dom import minidom

import requests
from docx import Document
from docx.document import Document as _Document
from docx.oxml import CT_P, CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph

from parser.schema import (
    Slotted, SciENcvProfile, Support, PersonMonth, Identification, Name)

CMD_ARGS = sys.argv
AMOUNT_EXTRACTOR = re.compile(r"\$?([\d,]+)")
DATE_EXTRACTOR = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}/\d{2,4})\s*[-–]\s*(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}/\d{2,4})"
)
YEAR_EXTRACTOR = re.compile(r"\b(20\d{2})\b")
FIELD_LABELS = {
    "section_header":        re.compile(r"^(ACTIVE|PENDING|IN-KIND)", re.IGNORECASE),
    "name_id":               re.compile(r"Name of Individual:\s*(.+?)(?:\s+Commons ID:.*)?$", re.IGNORECASE),
    "project_title":         re.compile(r"Title:\s*", re.IGNORECASE),
    "major_goals":           re.compile(r"Major Goals:\s*", re.IGNORECASE),
    "status":                re.compile(r"Status of Support:\s*", re.IGNORECASE),
    "role":                  re.compile(r"Role:\s*", re.IGNORECASE),
    "project_number":        re.compile(r"Project Number:\s*", re.IGNORECASE),
    "pd_pi":                 re.compile(r"Name of PD/PI:\s*", re.IGNORECASE),
    "source":                re.compile(r"Source of Support:\s*", re.IGNORECASE),
    "place":                 re.compile(r"(?:Primary )?Place of Performance:\s*", re.IGNORECASE),
    "dates":                 re.compile(r"Project.*?Date.*?:", re.IGNORECASE),
    "amount":                re.compile(r"Total Award Amount.*?:", re.IGNORECASE),
    "overlap":               re.compile(r"\*?Overlap\s*:\s*", re.IGNORECASE),
    "person_months_stopper": re.compile(r"Person\s*Months", re.IGNORECASE)
}
DATE_FORMATS = ["%m/%d/%Y", "%m/%d/%y", "%m/%Y", "%m/%y"]
TRANSLATION_TABLE = str.maketrans({
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '\u201c': '"',  # Left smart quote
        '\u201d': '"',  # Right smart quote
    })

DEFAULT_SUPPORT_TEMPLATE = {
    "projecttitle": "",
    "awardnumber": "",
    "supportsource": "",
    "location": "",
    "contributiontype": "award", # Default, overridden by logic
    "awardamount": "",
    "inkinddescription": "",
    "overallobjectives": "",
    "potentialoverlap": "None",
    "startdate": "",
    "enddate": "",
    "supporttype": "current",    # Default, overridden by logic
    "commitment": []             # List of dicts [{"year": "2025", "effort": "1.2"}]
}
"""This acts as the "schema" for the builder and is copied for each new project found."""


def to_xml(
        slotted_dc: Slotted,
        root_tag: Optional[str] = None) -> Generator[str, None, None]:
    """
    Base function to convert slotted dataclasses into XML.

    :param slotted_dc: A slotted dataclass from the schema.
    :param root_tag: Optional root tag for the initial parent.
    """
    if root_tag: # clean root tag first in case < or > accidentally included
        clean_tag = root_tag.removeprefix("<").removesuffix(">")
        yield f"<{clean_tag}>"

    if not hasattr(slotted_dc, "__slots__"):
        raise AttributeError(f"ERROR: {type(slotted_dc)} without __slots__ provided.")

    for tag in slotted_dc.__slots__:
        value = getattr(slotted_dc, tag)
        if value is None:                   # yield a closed tag
            continue
        elif hasattr(value, "to_xml"):      # call the custom to_xml() method for the class
            yield value.to_xml()
        elif hasattr(value, "__slots__"):   # convert children to xml recursively
            yield f"<{tag}>"
            yield from to_xml(value)
            yield f"</{tag}>"
        elif isinstance(value, list):       # wrap, then yield list of child nodes
            yield f"<{tag}>"
            for child in value:
                child_tag = child.__class__.__name__.lower()
                yield f"<{child_tag}>"
                yield from to_xml(child)
                yield f"</{child_tag}>"
            yield f"</{tag}>"
        else:                               # finally, yield base values as strings
            yield f"<{tag}>{html.escape(str(value))}</{tag}>"
    if root_tag:
        clean_tag = root_tag.removeprefix("<").removesuffix(">")
        yield f"</{clean_tag}>"

    
def prettify_xml(raw_xml, spaces=2):
    domified = minidom.parseString(raw_xml)
    pretty_xml = domified.toprettyxml(indent=" "*spaces)
    return pretty_xml


def clean_text(text: str) -> str:
    if not text: return ""
    return text.strip().translate(TRANSLATION_TABLE).strip(" *_")


def parse_date_str(date_str: str) -> str:
    if not date_str: return ""
    date_str = date_str.strip(" *_")
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(date_str, fmt)
            if "d" not in fmt: return dt.strftime("%Y-%m-%01")
            return dt.strftime("%Y-%m-%d")
        except ValueError: continue
    return ""


def extract_dates(text: str) -> tuple[str, str]:
    match = DATE_EXTRACTOR.search(text)
    if match:
        return parse_date_str(match.group(1)), parse_date_str(match.group(2))
    return "", ""


def iter_block_items(parent: _Document):
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    else:
        raise ValueError("Parent must be a Document object")
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _update_field(builder: dict, raw_key: str, text: str, append: bool = False):
    """
    Explicitly maps regex labels to builder fields using Python 3.10 match/case.
    """
    text = text.strip()
    if not text: return

    def set_val(field_name: str):
        current = str(builder.get(field_name, ""))
        if append and current:
            builder[field_name] = current + " " + text
        else:
            builder[field_name] = text

    match raw_key:
        case "project_title":   set_val("projecttitle")
        case "project_number":  set_val("awardnumber")
        case "source":          set_val("supportsource")
        case "place":           set_val("location")
        case "amount":          set_val("awardamount")
        case "major_goals":     set_val("overallobjectives")
        case "overlap":         set_val("potentialoverlap")
        case "dates":
            # Date logic is unique, so handled manually
            if not append:
                s, e = extract_dates(text)
                builder["startdate"] = s
                builder["enddate"] = e
        case _: pass


def _finalize_support(builder: dict) -> Support:
    """
    Consumes the builder dict and returns a valid Support object.
    Nested here to keep 'builder' logic self-contained.
    """
    raw_coms = builder.pop("commitment", [])
    final_coms = [
        PersonMonth(year=c["year"], amount=float(c["effort"]))
        for c in raw_coms
    ]
    return Support(
        commitment=final_coms,
        **builder
    )


def _reset_builder(current_section: str) -> dict:
    """Creates a fresh builder dict with defaults based on the section."""
    new_builder = DEFAULT_SUPPORT_TEMPLATE.copy()
    new_builder["commitment"] = []  # Ensure new list
    new_builder["contributiontype"] = "inkind" if current_section == "IN-KIND" else "award"
    new_builder["supporttype"] = "pending" if current_section == "PENDING" else "current"
    return new_builder


def _parse_name(text: str, name_parts: dict) -> bool:
    """Updates name_parts if text contains the name label. Returns True if found."""
    if name_match := FIELD_LABELS["name_id"].search(text):
        full_name = name_match.group(1).strip(" *_")
        if "," in full_name:
            parts = full_name.split(",", 1)
            name_parts["lastname"] = parts[0].strip()
            rest = parts[1].strip().split()
            if rest:
                name_parts["firstname"] = rest[0]
                name_parts["middlename"] = " ".join(rest[1:]) if len(rest) > 1 else ""
        else:
            parts = full_name.split(" ")
            if len(parts) == 2:
                name_parts["firstname"] = parts[0]
                name_parts["lastname"] = parts[1]
            else:
                name_parts["firstname"] = parts[0]
                name_parts["lastname"] = parts.pop()
                name_parts["middlename"] = "".join(parts[1:])
        return True
    return False


def _process_paragraph(text: str, builder: dict, last_field_key: Optional[str]) -> Optional[str]:
    """
    Scans paragraph text for field labels and updates the builder.
    Returns the last_field_key for context tracking.
    """
    matches = []
    for label_name, pattern in FIELD_LABELS.items():
        if label_name in ["section_header", "name_id"]: continue
        for m in pattern.finditer(text):
            matches.append({"start": m.start(), "end": m.end(), "raw_key": label_name})

    matches.sort(key=lambda x: x["start"])

    # CASE A: No new labels found, append to previous field
    if not matches:
        if last_field_key:
            _update_field(builder, last_field_key, text, append=True)
        return last_field_key

    # CASE B: Text exists before the first label
    if matches[0]["start"] > 0:
        pre_text = text[:matches[0]["start"]].strip(" *_")
        if pre_text and last_field_key:
            _update_field(builder, last_field_key, pre_text, append=True)

    # CASE C: Process Matches
    current_key = last_field_key
    for i, match in enumerate(matches):
        start_idx = match["end"]
        end_idx = matches[i + 1]["start"] if i + 1 < len(matches) else len(text)
        val = text[start_idx:end_idx].strip(" *_")

        current_key = match["raw_key"]
        _update_field(builder, current_key, val, append=False)

    return current_key


def _process_table(table: Table, builder: dict):
    """Extracts Year/Effort rows from a table and appends to builder."""
    rows = []
    start_row_index = 0
    if table.rows:
        first_row_text = "".join([c.text.lower() for c in table.rows[0].cells])
        if "year" in first_row_text or "month" in first_row_text:
            start_row_index = 1

    for row in table.rows[start_row_index:]:
        cells = [c.text.strip() for c in row.cells]
        if len(cells) >= 2:
            year_match = YEAR_EXTRACTOR.search(cells[0])
            year = year_match.group(1) if year_match else ""
            effort = cells[1].lower().replace("calendar", "").strip()
            if year and effort:
                rows.append({"year": year, "effort": effort})
    if rows:
        builder["commitment"].extend(rows)


def parse_docx(doc_input: str) -> SciENcvProfile:
    # 1. LOAD DOCUMENT OBJECT
    if str(doc_input).startswith("http"):
        r = requests.get(doc_input)
        r.raise_for_status()
        doc = Document(io.BytesIO(r.content))
    else:
        doc = Document(Path(doc_input).__str__())

    # 2. STATE INITIALIZATION
    name_parts = {"firstname": "", "middlename": "", "lastname": ""}
    parsed_supports: List[Support] = []

    current_section = "ACTIVE"
    builder = _reset_builder(current_section)
    builder_active = False  # Flag to ignore noise before first project
    last_field_key = None

    # 3. PARSING LOOP
    for block in iter_block_items(doc):

        # --- PARAGRAPH HANDLING ---
        if isinstance(block, Paragraph):
            text = clean_text(block.text)
            if not text:
                continue

            # A. Parse Name
            if _parse_name(text, name_parts):
                continue

            # B. Section Headers
            if FIELD_LABELS["section_header"].match(text):
                if builder_active:
                    parsed_supports.append(_finalize_support(builder))

                header = text.upper()
                current_section = "PENDING" if "PENDING" in header else "IN-KIND" if "IN-KIND" in header else "ACTIVE"
                # Reset for new section
                builder = _reset_builder(current_section)
                builder_active = False
                continue

            # C. New Project Detection
            if FIELD_LABELS["project_title"].search(text):
                if builder_active:
                    parsed_supports.append(_finalize_support(builder))

                # Start new project
                builder = _reset_builder(current_section)
                builder_active = True
                last_field_key = None  # Reset context for new project

            if not builder_active: continue

            # D. Field Extraction
            # Delegates complex regex logic to helper
            last_field_key = _process_paragraph(text, builder, last_field_key)

        # --- TABLE HANDLING ---
        elif isinstance(block, Table):
            if builder_active:
                _process_table(block, builder)

    # 4. FINAL FLUSH
    if builder_active:
        parsed_supports.append(_finalize_support(builder))

    return SciENcvProfile(
        identification=Identification(name=Name(**name_parts)),
        employment=[],
        funding=parsed_supports
    )


def main():
    if len(CMD_ARGS) < 2:
        raise OSError("Usage: python parse_os.py {path_to_docx}")
    else:
        arg = CMD_ARGS[1]
        doc_input = arg

    try:
        # parse
        profile = parse_docx(doc_input)
        # serialize
        xml_gen = to_xml(profile, root_tag="profile")
        xml_string = "".join(xml_gen)
        # prettify
        prettyxml = prettify_xml(xml_string)
        # print to console
        print(prettyxml)
        # write to file
        with open(profile.xml_file_name, "w") as f:
             f.write(prettyxml)

    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    main()
