# Minimal Sphinx makefile

SPHINXOPTS    ?=
SPHINXBUILD   ?= poetry run sphinx-build
SPHINXAUTOBUILD ?= poetry run sphinx-autobuild
SOURCEDIR     = source
BUILDDIR      = _build

.PHONY: help clean html live

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) -W || true
	@echo "Common targets: html, clean, live"

clean:
	rm -rf "$(BUILDDIR)"

html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

# Live-reloading server (requires sphinx-autobuild)
live:
	@$(SPHINXAUTOBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)

