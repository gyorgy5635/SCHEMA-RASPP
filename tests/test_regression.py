"""Regression tests for the Python 3 port of SCHEMA-RASPP.

The bundled beta-lactamase example (1G68.pdb, lac-msa.txt, PSE4-1G68.txt, lac-xo.txt)
is the reference. Golden fixtures in tests/golden/ were produced with the ORIGINAL
Python 2.7 upstream code and verified against an independent recomputation, so these
tests pin the port to the original tool's numerical behaviour.

Note: the RASPP-curve golden was regenerated with the Python 3 code AFTER making
raspp.curve() deterministic (it previously iterated a set, giving interpreter-
dependent tie-breaking). It differs from the raw Python 2 curve at exactly two
tied-energy points, where the deterministic version reports the strictly better
(lower average-mutation) library. See PORTING.md.
"""
import os, sys, subprocess
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOLDEN = os.path.join(HERE, "golden")


def run(*args):
    """Run a tool from the repo root and return (stdout) text."""
    p = subprocess.run([sys.executable, *args], cwd=ROOT,
                       capture_output=True, text=True)
    assert p.returncode == 0, f"{args} failed:\n{p.stderr}"
    return p.stdout


def run_py(snippet):
    """Run an inline snippet with cwd=ROOT so the repo's local `pdb`/`schema`/
    `raspp` modules import correctly (and don't shadow stdlib pdb in-process)."""
    p = subprocess.run([sys.executable, "-c", snippet], cwd=ROOT,
                       capture_output=True, text=True)
    assert p.returncode == 0, f"snippet failed:\n{p.stderr}"
    return p.stdout


def read(path):
    with open(path) as fh:
        return fh.read()


def strip_timing(text):
    return "\n".join(l for l in text.splitlines() if "took" not in l or "secs" not in l)


# ----------------------------------------------------------------- deterministic core
def test_pdbseq_matches_golden():
    out = run("pdbseq.py", "-pdb", "1G68.pdb")
    assert out.strip() == read(os.path.join(GOLDEN, "pdbseq.out")).strip()


def test_contacts_match_golden(tmp_path):
    out_file = tmp_path / "contacts.txt"
    run("schemacontacts.py", "-msa", "lac-msa.txt", "-pdb", "1G68.pdb",
        "-pdbal", "PSE4-1G68.txt", "-o", str(out_file))
    got = [l for l in read(str(out_file)).splitlines() if not l.startswith("#")]
    want = [l for l in read(os.path.join(GOLDEN, "contacts.txt")).splitlines()
            if not l.startswith("#")]
    assert got == want
    assert len(got) == 1040          # documented beta-lactamase contact count


def test_energies_match_golden():
    # Use the golden contact map so this test is independent of contact generation.
    out = run("schemaenergy.py", "-msa", "lac-msa.txt",
              "-con", os.path.join(GOLDEN, "contacts.txt"), "-xo", "lac-xo.txt",
              "-chim", "11111111", "22222222", "33333333",
              "13111111", "13121231", "22321222", "33213333", "-E", "-m")
    assert out.strip() == read(os.path.join(GOLDEN, "energies.out")).strip()


@pytest.mark.parametrize("chim,E", [
    ("11111111", 0), ("22222222", 0), ("33333333", 0),   # parents: no disruption
    ("13111111", 20), ("13121231", 107),                 # standard SCHEMA disruption
    ("22321222", 62), ("33213333", 67),
])
def test_schema_energy_values(chim, E):
    """Lock the standard SCHEMA disruption energies (the 2013 doc's 4/29/19/18 are
    stale; these values match the original code and an independent recomputation)."""
    out = run("schemaenergy.py", "-msa", "lac-msa.txt",
              "-con", os.path.join(GOLDEN, "contacts.txt"), "-xo", "lac-xo.txt",
              "-chim", chim, "-E")
    row = [l for l in out.splitlines() if l.startswith(chim)][0]
    assert int(row.split()[1]) == E


# ----------------------------------------------------------------- disruption semantics
def test_disruption_definition_unit():
    """getChimeraDisruption counts contacts whose residue pair is absent from ALL
    parents. Tiny hand-checked case (run in a subprocess; see run_py)."""
    out = run_py(
        "import schema\n"
        "parents=['AC','GD']; fragments=[(0,1),(1,2)]; contacts=[(0,1,1,2)]\n"
        # '11' -> pair (A,C) exists in parent 1 -> 0 ; '12' -> (A,D) in none -> 1
        "assert schema.getChimeraDisruption('11',contacts,fragments,parents)==0\n"
        "assert schema.getChimeraDisruption('12',contacts,fragments,parents)==1\n"
        "print('OK')\n")
    assert out.strip() == "OK"


# ----------------------------------------------------------------- RASPP determinism
def test_curve_tiebreak_deterministic_and_optimal():
    """raspp.curve() must be deterministic and, on an energy-tie within a bin,
    keep the lower average-mutation design. Fast: no RASPP search -- curve() takes
    the energy straight from its input tuples."""
    out = run_py(
        "import raspp, schema\n"
        "parents=[p for (k,p) in schema.readMultipleSequenceAlignmentFile(open('lac-msa.txt'))]\n"
        "c_hi=[50,100,150]; c_lo=[60,110,160]\n"
        "m_hi=schema.averageMutation(schema.getFragments(c_hi,parents[0]),parents)\n"
        "m_lo=schema.averageMutation(schema.getFragments(c_lo,parents[0]),parents)\n"
        "lo,hi=(c_lo,c_hi) if m_lo<m_hi else (c_hi,c_lo)\n"
        # both given the SAME energy; huge bin width forces them into one bin
        "res=[(5.0,hi,4,4),(5.0,lo,4,4)]\n"
        "o1=raspp.curve(list(res),parents,1e9); o2=raspp.curve(list(reversed(res)),parents,1e9)\n"
        "assert o1==o2, 'not deterministic'\n"
        "assert len(o1)==1 and abs(o1[0][1]-min(m_hi,m_lo))<1e-9, 'did not keep lower-m'\n"
        "print('OK')\n")
    assert out.strip() == "OK"


# ----------------------------------------------------------------- slow end-to-end
@pytest.mark.slow
def test_rasppcurve_end_to_end(tmp_path):
    out_file = tmp_path / "curve.txt"
    run("rasppcurve.py", "-msa", "lac-msa.txt",
        "-con", os.path.join(GOLDEN, "contacts.txt"),
        "-xo", "4", "-min", "10", "-o", str(out_file))
    got = strip_timing(read(str(out_file)))
    want = strip_timing(read(os.path.join(GOLDEN, "curve_xo4.txt")))
    assert got.strip() == want.strip()
    # determinism: a second run is byte-identical
    out_file2 = tmp_path / "curve2.txt"
    run("rasppcurve.py", "-msa", "lac-msa.txt",
        "-con", os.path.join(GOLDEN, "contacts.txt"),
        "-xo", "4", "-min", "10", "-o", str(out_file2))
    assert strip_timing(read(str(out_file2))).strip() == got.strip()
