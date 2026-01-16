import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional, Protocol, runtime_checkable, Union


@runtime_checkable
class Slotted(Protocol):
    __slots__: tuple[str, ...]


def to_xml(
        slotted_dc: Slotted,
        root_tag: Optional[str] = None) -> Generator[str, None, None]:
    """
    Base function to convert slotted dataclasses into XML.

    :param slotted_dc: A slotted dataclass from the schema.
    :param root_tag: Optional root tag for the initial parent.
    """
    if root_tag: # clean root tag first in case < or > accidentally included
        clean_tag = root_tag.removeprefix("<").removesuffix(">")
        yield f"<{clean_tag}>"

    if not hasattr(slotted_dc, "__slots__"):
        raise AttributeError(f"ERROR: {type(slotted_dc)} without __slots__ provided.")

    for tag in slotted_dc.__slots__:
        value = getattr(slotted_dc, tag)
        if value is None:                   # yield a closed tag
            yield f"<{tag}/>"
        elif hasattr(value, "to_xml"):      # call the custom to_xml() method for the class
            yield value.to_xml()
        elif hasattr(value, "__slots__"):   # convert children to xml recursively
            yield f"<{tag}>"
            yield from to_xml(value)
            yield f"</{tag}>"
        elif isinstance(value, list):       # wrap, then yield list of child nodes
            yield f"<{tag}>"
            for child in value:
                child_tag = child.__class__.__name__.lower()
                yield f"<{child_tag}>"
                yield from to_xml(child)
                yield f"</{child_tag}>"
            yield f"</{tag}>"
        else:                               # finally, yield base values as strings
            yield f"<{tag}>{html.escape(str(value))}</{tag}>"
    if root_tag:
        clean_tag = root_tag.removeprefix("<").removesuffix(">")
        yield f"</{clean_tag}>"


@dataclass(slots=True)
class Name:
    """
    Heirarchy:
        <profile> => <identification> => <name>
    """
    firstname: str
    middlename: str | None
    lastname: str

    def __post_init__(self):
        if not self.firstname: raise ValueError("No firstname provided.")
        if not self.lastname: raise ValueError("No lastname provided.")


@dataclass(slots=True)
class Identification:
    name: Name


@dataclass(slots=True)
class Year:
    year: int


@dataclass(slots=True)
class Organization:
    """Always associated with a Position."""
    orgname: str
    city: str
    stateorprovince: str
    country: str

    def __post_init__(self):
        for tag in self.__slots__:
            value = getattr(self, tag)
            if not value:
                setattr(self, tag, "") # sets to blank string if not present

@dataclass(slots=True)
class Position:
    """
    Heirarchy:
        <profile> => <identification> => <position>
    """
    positiontitle: str
    organization: Organization
    startdate: Year
    enddate: Optional[Union[Year, str]]

    def __post_init__(self):
        """Ensuring that enddate (if None) returns an empty string."""
        if self.enddate is None:
            self.enddate = ""
        if self.enddate and self.startdate.year > self.enddate.year:
            raise ValueError(f"Position start year is after end year for position {self.positiontitle}")


@dataclass(slots=True)
class PersonMonth:
    """
    Year is inserted into tag as attribute.
    e.g. <personmonth year="2025">12</personmonth>
    """
    year: str
    amount: float

    def to_xml(self) -> str:
        """Custom to_xml fx due to year being a property in xml tags."""
        return f'<personmonth year="{self.year}">{self.amount}</personmonth>'


@dataclass(slots=True)
class Support:
    projecttitle: str
    awardnumber: str
    supportsource: str
    location: str
    contributiontype: Literal["award", "inkind"]
    awardamount: str | int
    inkinddescription: Optional[str]
    overallobjectives: str
    potentialoverlap: str
    startdate: str
    enddate: str
    supporttype: Literal["current", "pending"]
    commitment: List[PersonMonth]

    def __post_init__(self):
        self.projecttitle = (self.projecttitle or "")[:300]
        self.awardnumber = (self.awardnumber or "")[:50]
        self.location = (self.location or "")[:60]
        self.supportsource = (self.supportsource or "")[:60]
        self.potentialoverlap = (self.potentialoverlap or "")[:5000]
        if not self.startdate: self.startdate = ""
        if not self.enddate: self.enddate = ""

        self._clean_amount()
        self._clean_enums()
        self._clean_inkind()
    
    def _clean_amount(self):
        raw_amt = str(self.awardamount) if self.awardamount is not None else ""
        clean_amt = re.sub(r"\D", "", raw_amt)  # Remove non-digits
        self.awardamount = clean_amt[:13]

    def _clean_inkind(self):
        ik_desc = self.inkinddescription or ""
        if self.contributiontype == "inkind":
            if not ik_desc and self.projecttitle:
                ik_desc = self.projecttitle
                self.inkinddescription = ik_desc[:500]
        else:
            self.inkinddescription = ""

    def _clean_enums(self):
        if self.contributiontype not in ["award", "inkind"]:
            self.contributiontype = "award"
        if self.supporttype not in ["current", "pending"]:
            self.supporttype = "current"


@dataclass(slots=True)
class SciENcvProfile:
    identification: Identification
    employment: List[Position]
    funding: List[Support]

    @property
    def last_name(self):
        return self.identification.name.lastname

    @property
    def first_name(self):
        return self.identification.name.firstname

    @property
    def xml_file_name(self):
        """Returns a filename dependent on the found first/last name and timestamp for uniqueness."""
        if self.first_name and self.last_name:
            name = self.last_name + "_" + self.first_name
        elif self.first_name and not self.last_name:
            name = self.first_name
        else:
            name = "no_name_found"
        timestamp = "_".join([
            part.split(".")[0].replace(":", "-")
            for part in datetime.now().isoformat().split("T")
            ])
        return name + "_" + timestamp + ".xml"
        


