import pytest

from src.schema import (
    SciENcvProfile,
    Identification, Name, Position, Organization, Year, Support, PersonMonth
)
from src.parser.from_docx import parse_docx
from src.parser.to_xml import to_xml


@pytest.fixture
def clean_profile_data():
    """Returns a minimal valid profile structure."""
    return SciENcvProfile(
        identification=Identification(
            name=Name(firstname="NCBI", middlename="S.", lastname="User")
        ),
        employment=[
            Position(
                positiontitle="Research Assistant",
                organization=Organization(
                    orgname="Sample Laboratories",
                    city="Bethesda",
                    stateorprovince="Maryland",
                    country="United States"
                ),
                startdate=Year(year=2015),
                enddate=Year(year=2025)
            )
        ],
        funding=[]  # Empty list to start
    )


# --- Tests ---

def test_full_xml_generation(clean_profile_data):
    """
    Verifies that the entire tree is serialized correctly, including nested recursion and list wrapping.
    """
    # Generate XML
    xml_gen = to_xml(clean_profile_data, root_tag="profile")
    xml_str = "".join(xml_gen)

    # Assertions
    assert "<profile>" in xml_str
    assert "<firstname>NCBI</firstname>" in xml_str
    assert "<orgname>Sample Laboratories</orgname>" in xml_str
    # Check proper nesting of Position -> StartDate -> Year
    assert "<startdate><year>2015</year></startdate>" in xml_str
    assert "</profile>" in xml_str


def test_support_validation_logic():
    """
    Checks if Support.__post_init__ correctly cleans data:
    1. Truncates strings
    2. Cleans money (removes $)
    3. Defaults missing dates
    """
    s = Support(
        projecttitle="A" * 500,  # Too long
        awardnumber="R01-555",
        supportsource="NIH",
        location="USA",
        contributiontype="award",
        awardamount="$3,000,000",  # Needs cleaning
        inkinddescription=None,
        overallobjectives="Test",
        potentialoverlap="None",
        startdate=None,  # Should default to ""
        enddate="2025-01-01",
        supporttype="current",
        commitment=[]
    )

    # 1. Check Truncation (limit 300)
    assert len(s.projecttitle) == 300

    # 2. Check Amount Cleaning
    assert s.awardamount == "3000000"

    # 3. Check Date Defaults
    assert s.startdate == ""
    assert s.enddate == "2025-01-01"


def test_person_month_attributes():
    """
    Verifies the custom to_xml method for PersonMonth
    handles attributes correctly.
    """
    pm = PersonMonth(year="2025", amount=3.5)
    xml = pm.to_xml()

    # Needs to match: <personmonth year="2025">3.5</personmonth>
    assert 'year="2025"' in xml
    assert '>3.5</personmonth>' in xml


def test_list_wrapping_logic(clean_profile_data):
    """
    Ensures lists (like employment) are wrapped in their field name
    tag <employment> and items are wrapped in their class name <position>.
    """
    xml_gen = to_xml(clean_profile_data)
    xml_str = "".join(xml_gen)

    # The list container
    assert "<employment>" in xml_str

    # The list item
    assert "<position>" in xml_str

    # Structure: <employment><position>...</position></employment>
    assert "<employment><position>" in xml_str


def test_formatting_escaping():
    """
    Ensures special characters (like & in company names) don't break XML.
    """
    org = Organization(
        orgname="R&D Services",
        city="Test",
        stateorprovince="Test",
        country="Test"
    )

    xml_gen = to_xml(org)
    xml_str = "".join(xml_gen)

    assert "R&amp;D Services" in xml_str
    assert "R&D" not in xml_str
