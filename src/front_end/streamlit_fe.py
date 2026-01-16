import io
import hashlib
import base64
import streamlit as st
from datetime import datetime

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

def trigger_auto_download(content: str, filename: str, content_hash: str):
    """Triggers an automatic download in the browser using JavaScript."""
    b64 = base64.b64encode(content.encode()).decode()
    dl_link = f'data:application/xml;base64,{b64}'
    # This JS snippet creates a hidden anchor, clicks it, and removes it.
    js = f"""
    <script>
        var link = document.createElement('a');
        link.href = '{dl_link}';
        link.download = '{filename}';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    </script>
    """
    st.components.v1.html(js, height=0)

def main():
    # Page Config
    st.set_page_config(page_title="NIH Other Support Converter", layout="wide")

    st.title("NIH Other Support Word => XML Converter")
    st.markdown("""
    Upload a Word Document (.docx) to generate the SciENcv XML. 
    This tool parses "Other Support" files and prepares them for upload to SciENcv.
    """)

    # Initialize Session State
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'last_converted_hash' not in st.session_state:
        st.session_state.last_converted_hash = None

    # Sidebar for History
    with st.sidebar:
        st.header("Conversion History")
        if st.session_state.history:
            if st.button("Clear History"):
                st.session_state.history = []
                st.session_state.last_converted_hash = None
                st.rerun()
            
            for idx, item in enumerate(reversed(st.session_state.history)):
                # Use the content hash + index to ensure stability and uniqueness
                content_hash = get_hash(item['xml'])
                unique_key = f"hist_{content_hash}_{idx}"
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
            pretty_xml, xml_filename = convert_docx_to_xml(file_bytes)
            
            content_hash = get_hash(pretty_xml)
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Store in history
            history_item = {
                "filename": uploaded_file.name,
                "xml_filename": xml_filename,
                "xml": pretty_xml,
                "timestamp": timestamp_str
            }
            # Avoid duplicate consecutive entries
            is_new_conversion = not st.session_state.history or st.session_state.history[-1]["xml"] != pretty_xml
            
            if is_new_conversion:
                st.session_state.history.append(history_item)
            
            # Check if we should trigger auto-download
            # We trigger it if this is a "new" conversion in this session
            if st.session_state.last_converted_hash != content_hash:
                trigger_auto_download(pretty_xml, xml_filename, content_hash)
                st.session_state.last_converted_hash = content_hash

            with col1:
                st.success(f"Conversion Successful: {xml_filename}")
                st.download_button(
                    label="Download XML (Manual)",
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
    else:
        # Reset last converted hash if no file is uploaded (to allow re-uploading same file)
        st.session_state.last_converted_hash = None

if __name__ == "__main__":
    main()
