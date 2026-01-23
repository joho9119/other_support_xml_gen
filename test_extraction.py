
import re

def original_logic(cells):
    year = re.sub(r"[^\d]", "", cells[0])
    effort = cells[1].lower().replace("calendar", "").strip()
    return year, effort

def improved_logic(cells):
    # Improved year extraction (keep just digits or maybe handle ranges?)
    year = re.sub(r"[^\d]", "", cells[0])
    
    # Improved effort extraction
    # We want to extract the number from strings like "2.0 CM", "1.5 months", "3.0 calendar months"
    effort_text = cells[1].lower().replace("calendar", "").replace("months", "").replace("cm", "").strip()
    # Or better, use a regex to find the first number
    match = re.search(r"(\d+\.?\d*)", effort_text)
    effort = match.group(1) if match else effort_text
    return year, effort

test_cases = [
    (["2024", "2.0 CM"], ("2024", "2.0")),
    (["2025", "1.5 months"], ("2025", "1.5")),
    (["2026", "3.0 calendar months"], ("2026", "3.0")),
    (["Year 1", "0.6 CM"], ("1", "0.6")),
]

print("Testing Original Logic:")
for cells, expected in test_cases:
    actual = original_logic(cells)
    print(f"Input: {cells} -> Actual: {actual}, Expected: {expected}, Match: {actual == expected}")

print("\nTesting Improved Logic:")
for cells, expected in test_cases:
    actual = improved_logic(cells)
    print(f"Input: {cells} -> Actual: {actual}, Expected: {expected}, Match: {actual == expected}")
