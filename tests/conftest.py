import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(ROOT, "tests", "golden")

# NOTE: we deliberately do NOT put ROOT on sys.path here. The repo ships a
# top-level module named `pdb.py` which would shadow the standard-library
# debugger `pdb` and break pytest itself. Tests invoke the tools via subprocess
# with cwd=ROOT, so the tools' own directory resolves the local `pdb` correctly
# without polluting this process. (Renaming pdb.py is a recommended follow-up.)


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: end-to-end RASPP runs (tens of seconds)")
