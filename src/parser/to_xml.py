import html
import re
from typing import Generator, Optional
from xml.dom import minidom

from src.schema import RenderEmptyMixin, Slotted, XMLGenerationError


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

    render_all = isinstance(slotted_dc, RenderEmptyMixin)

    for tag in slotted_dc.__slots__:
        try:
            value = getattr(slotted_dc, tag)
            is_empty = value is None or (isinstance(value, str) and value == "")

            if is_empty:
                if render_all:
                    yield f"<{tag}/>"
                else:
                    continue
                continue # Either skipped or emitted empty tag

            elif hasattr(value, "to_xml"):      # call the custom to_xml() method for the class
                yield value.to_xml()

            elif hasattr(value, "__slots__"):   # convert children to xml recursively
                yield f"<{tag}>"
                yield from to_xml(value)
                yield f"</{tag}>"

            elif isinstance(value, list):       # wrap, then yield list of child nodes
                yield f"<{tag}>"
                for child in value:
                    if hasattr(child, "to_xml"):
                        yield child.to_xml()
                    else:
                        child_tag = child.__class__.__name__.lower()
                        if hasattr(child, "__slots__"):
                            yield f"<{child_tag}>"
                            yield from to_xml(child)
                            yield f"</{child_tag}>"
                yield f"</{tag}>"
            else: # finally, yield base values as strings
                yield f"<{tag}>{html.escape(str(value))}</{tag}>"
        except Exception as e:
            if isinstance(e, XMLGenerationError):
                raise e
            raise XMLGenerationError(
                f"Failed to generate XML for tag '{tag}' in {type(slotted_dc).__name__}. "
                f"Value: {value!r}. Error: {e}"
            ) from e

    if root_tag:
        clean_tag = root_tag.removeprefix("<").removesuffix(">")
        yield f"</{clean_tag}>"


def prettify_xml(raw_xml, spaces=2):
    """Pretty prints but keeps data fields (like <year>2025</year>) on one line."""
    domified = minidom.parseString(raw_xml)
    pretty_xml = domified.toprettyxml(indent=" "*spaces)
    return re.sub(r'>\n\s+([^<>\n]+)\n\s*</', r'>\1</', pretty_xml)
