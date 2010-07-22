# $Id$
#
# bib2html ships with a file Named Makefile that is not very useful,
# so this file is named makefile instead to avoid confusion.

GENBST                          = ./gen-bst
MAKE                            = make
RM                              = rm -f

HTMLBST = html-a.bst html-aa.bst html-ac.bst html-aca.bst html-acr.bst html-acra.bst html-ar.bst html-ara.bst html-n.bst html-na.bst html-nc.bst html-nca.bst html-ncr.bst html-ncra.bst html-nr.bst html-nra.bst html-u.bst html-ua.bst 


default: ${HTMLBST}

${HTMLBST}:
	${GENBST}
	${MAKE} clean

clean:
	${RM} *~ syntax

output_clean:
	${RM} *.bst

really_clean: clean output_clean

.PHONY: default all clean output_clean really_clean
