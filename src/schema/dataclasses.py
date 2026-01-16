import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional, Protocol, runtime_checkable, Union


@runtime_checkable
class Slotted(Protocol):
    __slots__: tuple[str, ...]

class RenderEmptyMixin:
    """Signal to render all tags for the subclass, even if value is None."""
    pass

class SkipEmptyMixin:
    """Signal to skip empty tags for the subclass if value is None."""
    pass


@dataclass(slots=True)
class Name(SkipEmptyMixin):
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
        if not self.middlename: self.middlename = None


@dataclass(slots=True)
class Identification(SkipEmptyMixin):
    name: Name


@dataclass(slots=True)
class Year(SkipEmptyMixin):
    year: int


@dataclass(slots=True)
class Organization(SkipEmptyMixin):
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
class Position(SkipEmptyMixin):
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
class PersonMonth(SkipEmptyMixin):
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
class Support(RenderEmptyMixin):
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
        self.location = (self.location or "")[:60]
        self.supportsource = (self.supportsource or "")[:60]
        self.potentialoverlap = (self.potentialoverlap or "")[:5000]
        if not self.startdate: self.startdate = ""
        if not self.enddate: self.enddate = ""

        self._clean_award_number()
        self._clean_amount()
        self._clean_enums()
        self._clean_inkind()

    def _clean_award_number(self):
        clean_award_num = self.awardnumber.replace(" ", "")
        self.awardnumber = (clean_award_num or "N/A")[:50]
    
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
class SciENcvProfile(RenderEmptyMixin):
    identification: Identification
    employment: List[Position]
    funding: List[Support]

    @property
    def xml_file_name(self):
        """Returns a filename dependent on the found first/last name and timestamp for uniqueness."""
        last_name = self.identification.name.lastname
        first_name = self.identification.name.firstname
        if first_name and last_name:
            name = last_name + "_" + first_name
        elif first_name and not last_name:
            name = first_name
        else:
            name = "no_name_found"
        timestamp = "_".join([
            part.split(".")[0].replace(":", "-")
            for part in datetime.now().isoformat().split("T")
            ])
        return name + "_" + timestamp + ".xml"
        


