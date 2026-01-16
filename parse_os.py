import sys
from io import BytesIO
from pathlib import Path

import requests
from docx import Document

OTHER_SUPPORT_BLANK = "https://grants.nih.gov/sites/default/files/other-support-format-page-rev-10-2021.docx"
OTHER_SUPPORT_SAMPLE = "https://grants.nih.gov/sites/default/files/other-support-sample-7-20-2021.docx"
CMD_ARGS = sys.argv


def check_is_docx(doc_path):
    if not str(doc_path).lower().endswith(".docx"):
        raise TypeError("Provided Word doc must end in .docx")
    else:
        print("PASS: Document ends in .docx")




def get_document_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

def load_document(doc_input) -> Document:
    if str(doc_input).startswith("http"):
        print(f"Fetching document from URL: {doc_input}")
        doc_source = get_document_from_url(doc_input)
    else:
        check_is_docx(doc_input)
        doc_source = doc_input

    doc = Document(doc_source)
    print(f"Successfully loaded document. Paragraphs: {len(doc.paragraphs)}")
    return doc


def parse_other_support(doc_input):
    load_document(doc_input)


def main():
    if len(CMD_ARGS) < 2:
        print("Usage: python parse_os.py {path to OS document}")
    else:
        if CMD_ARGS[1:][0].lower() == "sample":
            doc_input = OTHER_SUPPORT_SAMPLE
        else:
            doc_input = CMD_ARGS[1:][0]
    parse_other_support(doc_input)


if __name__ == "__main__":
    main()
