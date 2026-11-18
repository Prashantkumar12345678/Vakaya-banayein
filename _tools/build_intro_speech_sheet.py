"""Build the current fixed-body intro speech sheet (v2).
Mouth visemes are independent of the three deliberate hand gestures.
"""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("build_intro_speech_v2.py")),run_name="__main__")
