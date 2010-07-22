# Makefile,v 1.12 2002/08/18 17:24:46 jbednar Exp
#
# Requires GNU make

# Files to process
FIGFILES = ${wildcard *.fig}
FIGEPSS  = ${subst .fig,.eps,${FIGFILES}}
FIGPDFS  = ${subst .fig,.pdf,${FIGFILES}}
FIGPNGS  = ${subst .fig,.png,${FIGFILES}}

# Default targets 
all: figoutput measuring-map.v3.png

figoutput: ${FIGPNGS}

# General rule for making .pdf out of .fig
#%.eps : %.fig
#	fig2dev -L eps $< > $@


#%.pdf : %.eps
#	./epstopdf $<

# Converting PDF to PNG
%.png : %.pdf
	convert $< $@

# Native xfig exporting to png
%.png : %.fig
	fig2dev -L png -S 4 -b 10 -m 0.60 $< > $@


# Cleanup

clean:
	${RM} *~ ${FIGPDFS} ${FIGPNGS}

output_clean:
	${RM} ${FIGEPSS} ${FIGPDFS} ${FIGPNGS} measuring-map.v3.png

really_clean: clean output_clean

.PHONY: all default clean output_clean really_clean
FORCE :

