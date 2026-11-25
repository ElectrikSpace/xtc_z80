# Basic Makefile for Beamer presentations
# Usage: ./in-docker make

TARGET = presentation
SOURCES = $(TARGET).tex

all: $(TARGET).pdf

$(TARGET).pdf: $(SOURCES)
	pdflatex $(TARGET).tex
	pdflatex $(TARGET).tex  # Re-run to resolve references

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.pdf *.vrb

.PHONY: all clean
