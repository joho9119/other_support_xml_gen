import sys
from pathlib import Path

def main() -> None:
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    app_path = project_root / "src" / "front_end" / "streamlit_fe.py"

    # If running inside Streamlit, just import and run the app logic
    # This prevents "Runtime instance already exists" error on platforms like Streamlit Cloud
    import streamlit as st
    runtime = getattr(st, "runtime", None)
    is_running_with_streamlit = False
    if runtime is not None and hasattr(runtime, "exists"):
        try:
            is_running_with_streamlit = runtime.exists()
        except Exception:
            is_running_with_streamlit = False

    if is_running_with_streamlit:
        from src.front_end.streamlit_fe import main as app_main
        app_main()
        return

    # Otherwise, launch Streamlit in a separate process to avoid shutdown loop errors
    import subprocess
    subprocess.run(
        ["streamlit", "run", str(app_path)],
        check=False
    )
    return


if __name__ == "__main__":
    main()
