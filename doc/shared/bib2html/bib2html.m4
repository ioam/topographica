m4_dnl bibtex.m4,v 1.0 2000/05/22 03:28:54 jbednar Exp
m4_dnl
m4_dnl Citation support using Bib2HTML
m4_dnl 
m4_dnl Uses LaTeX-like cite_named, nocite, and bibliography commands
m4_dnl to create a .aux file for an HTML file specification written in m4.  
m4_dnl Bib2HTML can then use the .aux file to create a references section.
m4_dnl 
m4_dnl At present, cite_named is not quite as powerful as LaTeX's cite, 
m4_dnl which is why it has a different name.  It requires that you make 
m4_dnl up the link text yourself -- perhaps someday a full cite that can
m4_dnl generate the link text for you will be supported as well, but 
m4_dnl that may be fairly difficult.
m4_dnl
m4_dnl Also provides support for just listing a set of publications,
m4_dnl e.g. for a homepage; see m4_bib2html_section.
m4_dnl
m4_dnl James A. Bednar
m4_dnl
m4_dnl Example usage: "m4 file.m4 > file.html"
m4_dnl where file.m4 contains a line: include(bib2html.m4)m4_dnl
m4_dnl
m4_dnl
m4_dnl
m4_dnl Suppress all output from this file so that we can use blank
m4_dnl lines freely between definitions
m4_divert(-1)

m4_dnl Change the quote marks to symbols never used for other
m4_dnl legitimate purposes to avoid conflicts
m4_dnl
m4_changequote(,)
m4_changequote([[, ]])m4_dnl

m4_dnl Disable pound-sign commenting since it is used in URLs
m4_changecom



m4_dnl Returns the basename of the source file from which it is called
m4_dnl Requires external basename shell command
m4_dnl
m4_define([[m4_sourcefile_basename]],  [[m4_esyscmd(echo -n `basename "m4___file__" ".m4"`)]])


m4_dnl Private variable: Location of the m4_bib2html command
m4_define([[m4_bib2html_command]],  [[env BIBINPUTS="~/lib/nn/bibs//:/u/nn/bibs//:" BSTINPUTS="~/lib/nn/tex//:/u/nn/tex//:" PATH="${NNDIR}/tex/bib2html/:/u/nn/tex/bib2html/:${PATH}:/lusr/tex/bin/" bib2html -b "-min-crossrefs=9999"]])
m4_dnl
m4_dnl Private variable: Name of the .aux file to use
m4_define([[m4_bib2html_aux_file]],  m4_sourcefile_basename.aux)
m4_dnl
m4_dnl Private variable: Name of the .tmp HTML file to use
m4_define([[m4_bib2html_tmp_file]],  m4_sourcefile_basename[[]].tmp)


m4_dnl This command must be called before any other m4_bib2html_ commands
m4_dnl
m4_define([[m4_bib2html_init]],  [[m4_dnl
m4_syscmd(rm -f m4_bib2html_aux_file)m4_dnl
m4_syscmd(rm -f m4_bib2html_tmp_file)m4_dnl
m4_syscmd(echo "<!-- BEGIN BIBLIOGRAPHY references -->" >> m4_bib2html_tmp_file)
m4_syscmd(echo "<!-- END BIBLIOGRAPHY references -->"   >> m4_bib2html_tmp_file)
]])


m4_dnl Adds the specified BibTeX key(s) to the .aux file without
m4_dnl generating any link or other text
m4_dnl 
m4_dnl Example: m4_bib2html_nocite(bednar:nc2000,sirosh:htmlbook96-article)
m4_dnl
m4_define([[m4_bib2html_nocite]],  [[m4_ifelse($#, 1, [[m4_dnl
m4_syscmd(echo "\citation{$1}" >> "m4_bib2html_aux_file")]], [[m4_dnl
m4_syscmd(echo "\citation{$1}" >> "m4_bib2html_aux_file")m4_bib2html_nocite(m4_shift($@))]])]])


m4_dnl Private helper function to make a single citation with the given label
m4_dnl
m4_define([[m4_bib2html_cite_single_link]], [[m4_bib2html_nocite($1)<a href="#$1">$2</a>]])


m4_dnl Adds the specified BibTeX key(s) to the .aux file and generates
m4_dnl a link with the given text, with no surrounding parentheses
m4_dnl
m4_dnl Example: m4_bib2html_npcite_named(bednar:nc2000,sirosh:htmlbook96-article)
m4_dnl 
m4_define([[m4_bib2html_npcite_named]],  [[m4_ifelse($#, 2, [[m4_bib2html_cite_single_link([[$1]],[[$2]])]], [[m4_bib2html_cite_single_link([[$1]],[[$2]]),
m4_bib2html_npcite_named(m4_shift(m4_shift($@)))]])]])m4_dnl

m4_dnl Adds the specified BibTeX key(s) to the .aux file and generates
m4_dnl a link with the given text
m4_dnl
m4_dnl Example: m4_bib2html_cite_named(bednar:nc2000,sirosh:htmlbook96-article)
m4_dnl
m4_define([[m4_bib2html_cite_named]], [[(m4_bib2html_npcite_named($@))]])m4_dnl


m4_dnl Generates the BibTeX bibliography in the location from which this 
m4_dnl routine is called.  The first argument is a list of .bib files, the
m4_dnl second is the (optional) name to use for the references section, and
m4_dnl the third (optional) is a list of arguments for the bib2html command.
m4_dnl
m4_dnl Example: m4_bib2html_bibliography_base([[nnstrings,nn]],References,-a)
m4_dnl 
m4_define([[m4_bib2html_bibliography_base]], [[m4_dnl
<h2>$2</h2>
m4_syscmd(echo -n "\bibdata{[[$1]]}" >> "m4_bib2html_aux_file")m4_dnl
m4_syscmd(m4_bib2html_command $3 -d references m4_bib2html_aux_file m4_bib2html_tmp_file)m4_dnl
m4_undivert(m4_bib2html_tmp_file)m4_dnl  Include the bib2html output
m4_syscmd(rm -f m4_bib2html_tmp_file)m4_dnl
m4_syscmd(rm -f m4_bib2html_aux_file)m4_dnl
]])

m4_dnl Typical wrapper for m4_bib2html_bibliography_base for backwards compatibility
m4_dnl
m4_dnl Example: m4_bib2html_bibliography(nnstrings,nn)
m4_dnl 
m4_define([[m4_bib2html_bibliography]], [[m4_bib2html_bibliography_base([[$*]],References,)]])

m4_dnl Macro for generating an entire section consisting of a list of
m4_dnl bibliography entries.  E.g.:
m4_dnl
m4_dnl m4_bib2html_section(Theses,[[bednar:bs93,bednar:phd02,bednar:aitr97]])
m4_dnl
m4_dnl They should get sorted by date automatically; to change that see the
m4_dnl other options for bib2html_bibliography_base below.
m4_dnl
m4_define([[m4_bib2html_section]],[[m4_dnl
m4_bib2html_init[[]]
m4_bib2html_nocite($2)
m4_bib2html_bibliography_base([[nnstrings,nnvita,nn]],[[$1]],-r -c)]])m4_dnl
m4_dnl 
m4_dnl Other possible formats:
m4_dnl m4_bib2html_bibliography(nnstrings,nn)
m4_dnl m4_bib2html_bibliography_base([[nnstrings,nn]],,-a -r)
m4_dnl m4_bib2html_bibliography_base([[nnstrings,nn]],,-r -c -s plain)


m4_dnl Restore ability to generate output
m4_dnl
m4_divert[[]]m4_dnl
