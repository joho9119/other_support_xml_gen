import io
import base64
import streamlit as st

from src.schema import WordParserError
from src.parser.from_docx import parse_docx
from src.parser.to_xml import prettify_xml, to_xml


@st.cache_data
def convert_docx_to_xml(file_bytes: bytes) -> dict:
    """Parses DOCX bytes and returns (pretty_xml, xml_filename)."""
    input_bytes = io.BytesIO(file_bytes)
    profile = parse_docx(input_bytes)
    filename = profile.xml_file_name

    # Generate XML
    raw_xml = "".join(to_xml(profile, root_tag="profile"))
    final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw_xml
    pretty_xml = prettify_xml(final_xml)

    b64_xml = base64.b64encode(pretty_xml.encode()).decode()
    href = f'data:application/xml;base64,{b64_xml}'

    return {
        "filename": filename,
        "xml": pretty_xml,
        "href": href,
        "id": filename + str(len(pretty_xml)) # Unique ID for state tracking
    }


def main():
    # Page Config
    st.set_page_config(page_title="NIH Other Support Converter", layout="wide")

    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "selected_record" not in st.session_state:
        st.session_state["selected_record"] = None
    if "last_uploaded_id" not in st.session_state:
        st.session_state["last_uploaded_id"] = None

    st.title("NIH Other Support Word => XML Converter")
    st.markdown("""
    Upload a Word Document (.docx) to generate the SciENcv XML. 
    This tool parses "Other Support" files and prepares them for upload to SciENcv.
    """)
    col_left, col_right = st.columns([1, 2])
    with col_left:
        # File Uploader
        st.subheader("Process File")
        uploaded_file = st.file_uploader("Choose a Word file", type="docx")
        if uploaded_file is not None:
            current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"

            if st.session_state["last_uploaded_id"] != current_file_id:
                try:
                    # Read file into memory and use cached converter
                    file_bytes = uploaded_file.getvalue()
                    record = convert_docx_to_xml(file_bytes)

                    if not any(d['id'] == record['id'] for d in st.session_state["history"]):
                        st.session_state["history"].append(record)

                    st.session_state["selected_record"] = record
                    st.session_state["last_uploaded_id"] = current_file_id
                    st.success(f"Processed: {record['filename']}")

                except Exception as e:
                    # User-friendly error message
                    if isinstance(e, WordParserError):
                        st.error(f"⚠️ {e}")
                    else:
                        st.error(f"⚠️ An unexpected error occurred: {e}")
                    
                    # Hidden technical details
                    with st.expander("Technical details (for support)"):
                        st.exception(e)

        st.divider()

        st.subheader("History")
        if not st.session_state["history"]:
            st.caption("No files processed yet")
        else:
            for record in reversed(st.session_state["history"]):
                # Create a button that, when clicked, updates the 'selected_record'
                if st.button(f"📄 {record['filename']}", key=f"btn_{record['id']}", use_container_width=True):
                    st.session_state["selected_record"] = record

    with col_right:
        st.subheader("View Pane")
        record = st.session_state["selected_record"]

        if record:
            h_col1, h_col2 = st.columns([3, 1])
            with h_col1:
                st.markdown(f"**Viewing:** `{record['filename']}`")
            with h_col2:
                # Direct HTML download link styled as a button
                st.markdown(
                    f'<a href="{record["href"]}" download="{record["filename"]}" style="text-decoration: none;">'
                    f'<div style="background-color: #ff4b4b; color: white; padding: 6px 12px; '
                    f'text-align: center; border-radius: 5px; font-weight: bold; font-size: 14px;">'
                    f'⬇ Download</div></a>',
                    unsafe_allow_html=True
                )

            # XML Preview
            st.code(record["xml"], language="xml", line_numbers=True)
        else:
            st.info("Upload a file or select from history to view content.")

if __name__ == "__main__":
    main()
