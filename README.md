# NIH Other Support XML Generator

A small/specialized tool to convert NIH "Other Support" Word documents (`.docx`) into SciENcv-compatible XML files. Given the tight turnaround on uploading Other Supports for the upcoming deadlines, I hope this gives everyone a jumping off point for easily uploading their other supports into SciENcv.

## Public access

This app is currently deployed on Streamlit at https://sciencv-other-support-generator.streamlit.app/.

## Using XML with SciENcv
- SciENcv [allows for XML upload](https://support.nlm.nih.gov/kbArticle/?pn=KA-05499) which can streamline data entry. 
- Northwestern has a [great guide](https://libguides.galter.northwestern.edu/SciENcv/NewCPOS) on how to upload data to SciENcv

## Key Features

- **Word to XML Conversion**: Automatically parses NIH Other Support Word documents and maps them to the SciENcv XML schema.
- **Data Cleaning**: Automatically formats and cleans data (e.g., removing spaces from award numbers, trimming text lengths) to comply with SciENcv requirements.

## 📁 Project Structure

```text
├── src/
│   ├── parser/
│   │   ├── from_docx.py    # Core logic for extracting data from .docx files
│   │   └── to_xml.py      # Logic for rendering dataclasses into SciENcv XML
│   ├── schema/
│   │   └── dataclasses.py # Data models (slotted dataclasses) for NIH structure
│   └── front_end/
│       └── streamlit_fe.py # Main Streamlit UI logic
├── streamlit_app.py        # Entry point for Streamlit (for local hosting)
├── run_streamlit.py       # Helper script to run the Streamlit app
└── requirements.txt        # Project dependencies
```

## 🧠 Core Logic & Entry Points

### Parsing Logic (`src/parser/from_docx.py`)
The parser uses `python-docx` to iterate through paragraphs and tables in the Word document. It identifies sections from the previous other support format ("Positions", "Current Support", and "Pending Support") and maps them to the new SciENcv categories.

### Data Model (`src/schema/dataclasses.py`)
Profiles are mapped to basic dictionaries and then validated using dataclasses in ``__post_init__``. 

Structured dataclasses are: 
- `SciENcvProfile`: The root container for Identification, Employment, and Funding.
- `Support`: Represents individual grant/award entries with automated cleaning for award numbers and amounts.
- `PersonMonth`: Handles the mapping of year-based effort commitments.

### XML Generation (`src/parser/to_xml.py`)
A custom recursive generator (`to_xml`) converts the slotted dataclasses directly into the target XML format, which ensures that the tags match the SciENcv schema.

### Entry Points
- **Web App**: `streamlit_app.py` is the primary entry point for launching the conversion tool.
- **Programmatic**: `src.parser.from_docx.parse_docx` can be used to parse a file and return a `SciENcvProfile` object.

## 🛠️ How to Run

### Local Execution
1. **Install dependencies**:
   It is recommended to use [uv](https://github.com/astral-sh/uv) for fast, reliable dependency management.
   ```bash
   uv sync
   ```
2. **Run the application**:
   ```bash
   uv run python streamlit_app.py
   ```
   Or simply:
   ```bash
   uv run streamlit run src/front_end/streamlit_fe.py
   ```

## Acknowledgments
A very big thank you to the `python-docx` folks. This would not be doable without the heavy lifting of the contributors maintaining that library!

## 🔗 References
- [SciENcv XML Documentation](https://support.nlm.nih.gov/kbArticle/?pn=KA-05499)
- [NIH Other Support Format Page](https://grants.nih.gov/grants-process/write-application/forms-directory/other-support)
- [NIH Other Support Sample](https://grants.nih.gov/sites/default/files/other-support-sample-7-20-2021.docx)

