
import pytest
from src.schema import (
    SciENcvProfile, Identification, Name, Support, PersonMonth,
    XMLGenerationError, DocxParsingError
)
from src.parser.to_xml import to_xml
from src.parser.from_docx import _finalize_support, parse_docx
import io

def test_to_xml_error_context():
    # Create a dummy object that will fail during attribute access or serialization
    class BadValue:
        def __str__(self):
            raise RuntimeError("String conversion failed")
            
    class MockSlotted:
        __slots__ = ("faulty_tag",)
        def __init__(self):
            self.faulty_tag = BadValue()
            
    mock_obj = MockSlotted()
    
    with pytest.raises(XMLGenerationError) as excinfo:
        "".join(to_xml(mock_obj))
    
    assert "Failed to generate XML for tag 'faulty_tag' in MockSlotted" in str(excinfo.value)
    assert "String conversion failed" in str(excinfo.value)

def test_finalize_support_error_context():
    builder = {
        "projecttitle": "Faulty Project",
        "awardnumber": "123",
        "supportsource": "NIH",
        "location": "USA",
        "contributiontype": "award",
        "awardamount": "invalid_amount", # Support expects str|int but cleans it, let's try something else
        "overallobjectives": "Test",
        "potentialoverlap": "None",
        "startdate": "2023-01-01",
        "enddate": "2024-01-01",
        "supporttype": "current",
        "commitment": [{"year": "2023", "effort": "not_a_float"}] # This will fail in _finalize_support
    }
    
    with pytest.raises(DocxParsingError) as excinfo:
        _finalize_support(builder)
        
    assert "Could not process support entry for project 'Faulty Project'" in str(excinfo.value)
    assert "not_a_float" in str(excinfo.value)

def test_parse_docx_error_with_item_number():
    from unittest.mock import patch, MagicMock
    from src.parser.from_docx import Paragraph

    mock_doc = MagicMock()
    with patch("src.parser.from_docx.Document", return_value=mock_doc), \
         patch("src.parser.from_docx._iter_block_items") as mock_iter:
        
        # Mocking block that will fail
        bad_element = MagicMock()
        bad_block = Paragraph(bad_element, mock_doc)
        
        # Use a property mock for text if needed, but Paragraph.text access might be what we want to fail
        # Actually, let's make _clean_text fail when it receives the text
        mock_iter.return_value = [bad_block]
        
        with patch("src.parser.from_docx._clean_text", side_effect=RuntimeError("Cleaning failed")):
            with pytest.raises(DocxParsingError) as excinfo:
                parse_docx("dummy.docx")
            
            assert "Error at document item #0" in str(excinfo.value)
            assert "Cleaning failed" in str(excinfo.value)

if __name__ == "__main__":
    # Manual run if needed
    pass
