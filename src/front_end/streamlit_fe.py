import io
import streamlit as st
from datetime import datetime

from src.parser.from_docx import parse_docx
from src.parser.to_xml import prettify_xml, to_xml

@st.cache_data
def convert_docx_to_xml(file_bytes: bytes) -> tuple[str, str, str]:
    """Parses DOCX bytes and returns (pretty_xml, xml_filename, timestamp)."""
    input_bytes = io.BytesIO(file_bytes)
    profile = parse_docx(input_bytes)
    
    # Generate XML
    raw_xml = "".join(to_xml(profile, root_tag="profile"))
    final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw_xml
    pretty_xml = prettify_xml(final_xml)
    
    xml_filename = profile.xml_file_name
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    return pretty_xml, xml_filename, timestamp_str

def main():
    # Page Config
    st.set_page_config(page_title="NIH Other Support Converter", layout="wide")

    st.title("NIH Other Support Word => XML Converter")
    st.markdown("""
    Upload a Word Document (.docx) to generate the SciENcv XML. 
    This tool parses "Other Support" files and prepares them for upload to SciENcv.
    """)

    # Initialize Session State for history
    if 'history' not in st.session_state:
        st.session_state.history = []

    # Sidebar for History
    with st.sidebar:
        st.header("Conversion History")
        if st.session_state.history:
            if st.button("Clear History"):
                st.session_state.history = []
                st.rerun()
            
            for idx, item in enumerate(reversed(st.session_state.history)):
                # Use a more unique key based on the timestamp/filename to avoid collision during re-renders
                # and to help Streamlit track the media file correctly.
                unique_key = f"hist_{item['timestamp']}_{idx}"
                with st.expander(f"{item['filename']} ({item['timestamp']})"):
                    st.download_button(
                        label="Download Again",
                        data=item['xml'],
                        file_name=item['xml_filename'],
                        mime="application/xml",
                        key=unique_key
                    )
        else:
            st.info("No history yet. Convert a file to see it here.")

    # Main Interface
    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader("Choose a Word file", type="docx")

    if uploaded_file is not None:
        try:
            # Read file into memory and use cached converter
            file_bytes = uploaded_file.getvalue()
            pretty_xml, xml_filename, timestamp_str = convert_docx_to_xml(file_bytes)
            
            # Store in history
            history_item = {
                "filename": uploaded_file.name,
                "xml_filename": xml_filename,
                "xml": pretty_xml,
                "timestamp": timestamp_str.replace("_", " ") # Display format
            }
            # Avoid duplicate consecutive entries
            if not st.session_state.history or st.session_state.history[-1]["xml"] != pretty_xml:
                st.session_state.history.append(history_item)

            with col1:
                st.success(f"Conversion Successful: {xml_filename}")
                st.download_button(
                    label="Download XML",
                    data=pretty_xml,
                    file_name=xml_filename,
                    mime="application/xml",
                    key=f"main_download_{timestamp_str}"
                )

            with col2:
                st.subheader("XML Preview")
                st.code(pretty_xml, language="xml")

        except Exception as e:
            st.error(f"Error parsing file: {e}")
            st.exception(e)

if __name__ == "__main__":
    main()
