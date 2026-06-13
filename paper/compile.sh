#!/usr/bin/env bash
# Compile the paper to PDF (needs a TeX distribution: pdflatex + bibtex).
set -e
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode truthhire_paper.tex
bibtex truthhire_paper
pdflatex -interaction=nonstopmode truthhire_paper.tex
pdflatex -interaction=nonstopmode truthhire_paper.tex
echo "Built truthhire_paper.pdf"
