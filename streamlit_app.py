import inspect
import sys
from pathlib import Path
from streamlit.web import bootstrap

def main() -> None:
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    app_path = project_root / "src" / "front_end" / "streamlit_fe.py"

    # If running inside Streamlit, just import and run the app logic
    # This prevents "Runtime instance already exists" error on platforms like Streamlit Cloud
    import streamlit as st
    if st._is_running_with_streamlit:
        from src.front_end.streamlit_fe import main as app_main
        app_main()
        return

    # Otherwise, bootstrap the streamlit runtime (standard for local execution via `python streamlit_app.py`)
    run_sig = inspect.signature(bootstrap.run)
    kwargs = {}

    if "main_script_path" in run_sig.parameters:
        kwargs["main_script_path"] = str(app_path)
    else:
        kwargs["path"] = str(app_path)

    if "command_line" in run_sig.parameters:
        kwargs["command_line"] = "streamlit run"
    if "args" in run_sig.parameters:
        kwargs["args"] = []
    if "flag_options" in run_sig.parameters:
        kwargs["flag_options"] = {}
    if "is_hello" in run_sig.parameters:
        kwargs["is_hello"] = False

    bootstrap.run(**kwargs)


if __name__ == "__main__":
    main()
