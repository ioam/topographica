# Makefile for doc directory
# Does not currently make the reference manual, so that
# the documentation can be compiled even if the code won't.

RM                              = rm -f
PHP                             = php -q
SED                             = sed
LN                              = ln -s
M4                              = m4 -P
MAKE                            = make

M4BASE = ${wildcard */*_text.php.m4}

PHPBASE = ${wildcard */*_text.php} ${subst .php.m4,.php,${M4BASE}}
PHPHTML = ${subst _text.php,.html,${PHPBASE}}

# Can also add --graph=callgraph to show who called what, but only for a specific simulation run
# or --graph=all
EPYDOC = bin/epydoc
CALLEPYDOC = env PYTHONPATH=external/param:external/imagen:external/paramtk: ${EPYDOC} --dotpath=/usr/bin/dot --graph=classtree --inheritance=listed --docformat=ReStructuredText --show-sourcecode --html 

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

# Doesn't currently build Lancet manual by default
reference-manual: Param_Reference/index.html ParamTk_Reference/index.html Imagen_Reference/index.html Reference_Manual/toc.html

Reference_Manual/toc.html: ../topo/*.py ../topo/*/*.py ../external/param/param/*.py ../external/paramtk/paramtk/*.py ../external/imagen/numbergen/*.py  ../external/imagen/imagen/*.py Reference_Manual/index_text.php
	cd .. ; ${CALLEPYDOC} -o doc/Reference_Manual --exclude=topo.tests --name=IOAM --url=http://ioam.github.com topo external/param/param external/paramtk/paramtk external/imagen/numbergen external/imagen/imagen
	mv Reference_Manual/index.html Reference_Manual/hierarchy.html
	make Reference_Manual/index.html

Param_Reference/index.html: ../external/param/param/*.py
	cd .. ; ${CALLEPYDOC} -o doc/Param_Reference --name=Param --url=http://ioam.github.com/param external/param/param

ParamTk_Reference/index.html: ../external/paramtk/paramtk/*.py
	cd .. ; ${CALLEPYDOC} -o doc/ParamTk_Reference --name=ParamTk --url=http://ioam.github.com/paramtk external/paramtk/paramtk

Imagen_Reference/index.html: ../external/imagen/numbergen/*.py  ../external/imagen/imagen/*.py
	cd .. ; ${CALLEPYDOC} -o doc/ImaGen_Reference --name=ImaGen --url=http://ioam.github.com/imagen external/imagen/imagen

Lancet_Reference/index.html: ../external/lancet/lancet/*.py
	cd .. ; ${CALLEPYDOC} -o doc/Lancet_Reference --name=Lancet --url=http://github.com/ioam/lancet external/lancet/lancet




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
	${RM} -r *_Reference/

.PHONY: default all clean clean-php

