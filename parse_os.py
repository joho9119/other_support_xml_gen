import sys
import io
from pathlib import Path

import requests
from docx import Document
from docx.document import Document as _Document

OTHER_SUPPORT_BLANK = "https://grants.nih.gov/sites/default/files/other-support-format-page-rev-10-2021.docx"
OTHER_SUPPORT_SAMPLE = "https://grants.nih.gov/sites/default/files/other-support-sample-7-20-2021.docx"
CMD_ARGS = sys.argv


def load_document(doc_input) -> _Document:
    if str(doc_input).startswith("http"):
        print(f"Fetching document from URL: {doc_input}")
        response = requests.get(doc_input)
        response.raise_for_status()
        doc_source = io.BytesIO(response.content)
    else:
        if not str(doc_input).lower().endswith(".docx"):
            raise TypeError("Provided Word doc must end in .docx")
        doc_path = Path(doc_input)
        doc_path.is_file()
        if not doc_path.is_file():
            if not doc_path.exists():
                raise ValueError(f"Provided input does not point to a valid file path. (Input: {doc_input}")
            if doc_path.is_dir():
                raise TypeError(f"Provided input must point to a file. (Pointing to folder: {doc_path.name}).")
        doc_source = doc_path

    doc = Document(doc_source)
    print(f"Successfully loaded document. Paragraphs: {len(doc.paragraphs)}")
    return doc


def parse_other_support(doc_input):
    word_doc = load_document(doc_input)
    print(f"File loaded: {word_doc.paragraphs}")


def main():
    if len(CMD_ARGS) < 2:
        print("Usage: python parse_os.py {path to OS document}")
        return
    else:
        if CMD_ARGS[1:][0].lower() == "sample":
            doc_input = OTHER_SUPPORT_SAMPLE
        else:
            doc_input = CMD_ARGS[1:][0]
    parse_other_support(doc_input)


if __name__ == "__main__":
    main()
