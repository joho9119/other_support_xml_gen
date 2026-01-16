from parser.from_docx import parse_docx
from parser.from_docx.src import to_xml, prettify_xml

def main():
    OTHER_SUPPORT_SAMPLE = "https://grants.nih.gov/sites/default/files/other-support-sample-7-20-2021.docx"
    print(f"Fetching document from URL: {OTHER_SUPPORT_SAMPLE}")
    
    try:
        # parse
        profile = parse_docx(OTHER_SUPPORT_SAMPLE)
        # serialize
        xml_gen = to_xml(profile, root_tag="profile")
        xml_string = "".join(xml_gen)

        prettyxml = prettify_xml(xml_string)
        # print to console
        print(prettyxml)
        # write to file
        with open(profile.xml_file_name, "w") as f:
             f.write(prettyxml)

    except Exception as e:
        print(f"Error processing file: {e}")
        print(f"XML generated: {xml_string}")


if __name__ == "__main__":
    main()
