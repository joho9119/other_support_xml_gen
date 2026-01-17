import io
import hashlib
import streamlit as st

from src.parser.from_docx import parse_docx
from src.parser.to_xml import prettify_xml, to_xml

@st.cache_data
def convert_docx_to_xml(file_bytes: bytes) -> tuple[str, str]:
    """Parses DOCX bytes and returns (pretty_xml, xml_filename)."""
    input_bytes = io.BytesIO(file_bytes)
    profile = parse_docx(input_bytes)
    
    # Generate XML
    raw_xml = "".join(to_xml(profile, root_tag="profile"))
    final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw_xml
    pretty_xml = prettify_xml(final_xml)
    
    xml_filename = profile.xml_file_name
    
    return pretty_xml, xml_filename

def get_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()

def main():
    # Page Config
    st.set_page_config(page_title="NIH Other Support Converter", layout="wide")

    st.title("NIH Other Support Word => XML Converter")
    st.markdown("""
    Upload a Word Document (.docx) to generate the SciENcv XML. 
    This tool parses "Other Support" files and prepares them for upload to SciENcv.
    """)

    # Main Interface
    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader("Choose a Word file", type="docx")

    if uploaded_file is not None:
        try:
            # Read file into memory and use cached converter
            file_bytes = uploaded_file.getvalue()
            pretty_xml, xml_filename = convert_docx_to_xml(file_bytes)
            
            content_hash = get_hash(pretty_xml)

            with col1:
                st.success(f"Conversion Successful: {xml_filename}")
                st.download_button(
                    label="Download XML",
                    data=pretty_xml,
                    file_name=xml_filename,
                    mime="application/xml",
                    key=f"main_download_{content_hash}"
                )

            with col2:
                st.subheader("XML Preview")
                st.code(pretty_xml, language="xml")

        except Exception as e:
            st.error(f"Error parsing file: {e}")
            st.exception(e)

if __name__ == "__main__":
    main()
