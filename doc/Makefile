# Makefile for doc directory
# Does not currently make the reference manual, so that
# the documentation can be compiled even if the code won't.

# $Id$

RM                              = rm -f
PHP                             = php -q
SED                             = sed
LN                              = ln -s
M4                              = m4 -P
MAKE                            = make

M4BASE = ${wildcard */*_text.php.m4}

PHPBASE = ${wildcard */*_text.php} ${subst .php.m4,.php,${M4BASE}}
PHPHTML = ${subst _text.php,.html,${PHPBASE}}


# General rule based only on target filename and location

# Old version: worked only for text.php -> index.html
#%/index.html : %/text.php shared/*.php shared/*.css
#	cd $* ; ${PHP} ../shared/index.php > index.html

# Works for any *_text.php -> *.html
# Hack: passes in text filename in an arbitrary php.ini option named
# 'sendmail_from', because it's not clear how to pass in 
# a user-defined variable value
%.html : %_text.php shared/*.php shared/*.css
	cd ${dir $@} ; ${PHP} -d sendmail_from=${notdir $<} ../shared/index.php > $(subst _text.php,.html,${notdir $<})


# PHP files can be preprocessed with M4 if desired.
%.php : %.php.m4 shared/bib2html.m4
	${M4} $< > $@

# Generate HTML files from source versions
default: bib2html imagedirs all
all: ${PHPHTML}

# Extra dependency
Home/index.html: Home/news_text.php

# Can also add --graph=callgraph to show who called what, but only for a specific simulation run
reference-manual: Reference_Manual/toc.html
Reference_Manual/toc.html: ../topo/*.py ../topo/*/*.py ../param/*.py Reference_Manual/index_text.php
	-mv ../topo/tests ../topo-tests-tmp
	cd .. ; bin/epydoc --graph=classtree --inheritance=listed --docformat=ReStructuredText --show-sourcecode --html -o doc/Reference_Manual --name=Topographica --url=http://topographica.org topo param
	mv ../topo-tests-tmp ../topo/tests 
# CEBALERT: shoud topo.html be topographica.html or maybe hierarchy.html?
	mv Reference_Manual/index.html Reference_Manual/topo.html
	make Reference_Manual/index.html
# 	--graph=all

imagedirs:
	${MAKE} -C User_Manual/images/


bib2html:
	${MAKE} -C shared/bib2html/

clean:

# Not removed by default, for people who do not have PHP locally
clean_php:
	${RM} ${PHPHTML}
	${RM} .??*~ *~ */*~ */.??*~ reference-manual
	${RM} Reference_Manual/*.html Reference_Manual/*.css Reference_Manual/*.png Reference_Manual/*.js

.PHONY: default all clean clean-php

