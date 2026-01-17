import io
import base64
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

def main():
    # Page Config
    st.set_page_config(page_title="NIH Other Support Converter", layout="centered")

    st.title("NIH Other Support Word => XML Converter")
    st.markdown("""
    Upload a Word Document (.docx) to generate the SciENcv XML. 
    This tool parses "Other Support" files and prepares them for upload to SciENcv.
    """)

    # File Uploader
    uploaded_file = st.file_uploader("Choose a Word file", type="docx")

    if uploaded_file is not None:
        try:
            # Read file into memory and use cached converter
            file_bytes = uploaded_file.getvalue()
            pretty_xml, xml_filename = convert_docx_to_xml(file_bytes)
            
            st.success(f"Conversion Successful: {xml_filename}")
            
            # Create a direct download link using Data URI (bypasses Streamlit's internal storage)
            b64_xml = base64.b64encode(pretty_xml.encode()).decode()
            href = f'data:application/xml;base64,{b64_xml}'
            
            # Styled Link Button
            st.markdown(
                f'<a href="{href}" download="{xml_filename}" style="text-decoration: none;">'
                f'<div style="background-color: #ff4b4b; color: white; padding: 10px 20px; '
                f'text-align: center; border-radius: 5px; font-weight: bold; '
                f'display: inline-block; cursor: pointer;">'
                f'Download XML File</div></a>',
                unsafe_allow_html=True
            )

            st.divider()

            # XML Preview & Copy
            st.subheader("XML Preview & Copy")
            st.info("💡 You can copy the XML below by clicking the copy icon in the top-right corner of the code box.")
            st.code(pretty_xml, language="xml")

        except Exception as e:
            st.error(f"Error parsing file: {e}")
            st.exception(e)

if __name__ == "__main__":
    main()
