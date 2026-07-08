import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(ROOT, "tests", "golden")

# Tests invoke the tools via subprocess with cwd=ROOT, matching real usage, so we
# do not need ROOT on sys.path here. (The former pdb.py/stdlib-pdb shadowing that
# broke `python -m pytest` was resolved by renaming pdb.py -> pdbfile.py.)


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: end-to-end RASPP runs (tens of seconds)")
