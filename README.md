SCHEMA-RASPP
============

This is a software package for protein engineers. It uses protein structure and sequence information to aid researchers in designing protein recombination libraries.

These tools can calculate SCHEMA energies of chimeric proteins and run the RASPP algorithm to find optimal library designs. The package includes documentation and examples. 

SCHEMA was developed in the laboratory of Frances H. Arnold at the California Institute of Technology.

Python 3
--------

This fork runs on Python 3 (tested on 3.9–3.13); the original tools targeted
Python 2. The port is verified byte-for-byte against the original Python 2.7
output on the bundled β-lactamase example, and `raspp.curve()` was made
deterministic. See **PORTING.md** for details and the note that the values in
`schema-tools-doc.html` are stale illustrations.

Install (optional; also runnable directly as `python <script>.py`):

    pip install .            # or  pip install -e ".[test]"  for development

This installs console commands `schema-contacts`, `schema-energy`,
`schema-rasppcurve`, `schema-random`, and `schema-pdbseq`.

Quick start (β-lactamase example — using the scripts directly):

    python schemacontacts.py -msa lac-msa.txt -pdb 1G68.pdb -pdbal PSE4-1G68.txt -o contacts.txt
    python schemaenergy.py  -msa lac-msa.txt -con contacts.txt -xo lac-xo.txt -chim 13111111 13121231 -E -m
    python rasppcurve.py    -msa lac-msa.txt -con contacts.txt -xo 7 -min 4 -o curve.txt

Tests:

    pytest            # fast regression suite (~2 s)
    pytest -m slow    # end-to-end RASPP curve (~1 min)

References:

Voigt, C. et al., "Protein building blocks preserved by recombination," Nature Structural Biology 9(7):553-558 (2002).
Meyer, M. et al., "Library analysis of SCHEMA-guided recombination," Protein Science 12:1686-1693 (2003).
Otey, C. et al., "Functional evolution and structural conservation in chimeric cytochromes P450: Calibrating a structure-guided approach," Chemistry & Biology 11:1-20 (2004)
Silberg, J. et al., "SCHEMA-guided protein recombination," Methods in Enzymology 388:35-42 (2004).
Endelman, J. et al., "Site-directed protein recombination as a shortest-path problem," Protein Engineering, Design & Selection 17(7):589-594 (2005).


