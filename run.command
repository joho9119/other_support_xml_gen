#!/bin/bash
cd "$(dirname "$0")"
uv sync
uv run python run_streamlit.py
