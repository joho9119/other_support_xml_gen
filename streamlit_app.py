import sys
from pathlib import Path

# Add the project root to sys.path so that Streamlit can import 'src' correctly.
root_path = Path(__file__).parent.resolve()
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from src.front_end.streamlit_fe import main

if __name__ == "__main__":
    main()
