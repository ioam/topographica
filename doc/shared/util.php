<?php

### JABALERT: 
### Should add a function to fill in the appropriate href file 
### extension (.php or .html), overridable from the command line.
### Then pages could be served either statically, as now, or 
### dynamically.


############################################################################
#       find current folder name
############################################################################
function folder_name() {

  $fname = $_SERVER['PWD'];
  $fname = preg_replace('|.*/|',"/",$fname);
  return $fname;
}

############################################################################
#       find current folder name, ready for displaying to the screen
############################################################################
function bare_folder_name() {

  $fname = $_SERVER['PWD'];
  $fname = preg_replace('|.*/|',"",$fname);
  $fname = preg_replace('|_|'," ",$fname);
  return $fname;
}

############################################################################
#       banner
############################################################################
function banner($fname) {

  include('config.php');
    
  if ($fname == "/Home")  {
	
	# main page banner
	print '
<table width="100%" cellpadding="20"><tr><td bgcolor="'.$banner_bg_color.'">
<CENTER>
<IMG src="../images/'.$logofile.'" align="middle"
     width="497" height="134" border="0" alt="Topographica logo">
</CENTER>
</td></tr></table>
';

  } else {

	# subdirectory page banner
	$pwd = bare_folder_name();

	print '
<table width="100%" cellpadding="20"><tr><td bgcolor="'.$banner_bg_color.'">
<CENTER>
<table border=0 width="420" height="113" background="../images/topo-subbanner-bg.png"><tr><td><center>
<font size="+11"><i>&nbsp;</font><!-- Moves text down slightly -->
<font size="+3" face="serif" font-style="italic"><i>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'.$pwd.'</i></font></center>
</td></tr></table>
</CENTER>
</td></tr></table>
';
  }

}

############################################################################
#        menu 
############################################################################
function menu_side($fname) {

	include('config.php');

	# menu name and link
	$menu_items = array("Home" => "../Home/index.html", 
#		"Screenshots" => "../Screenshots/index.html",
		"News" => "../News/index.html",
		"Downloads" => "../Downloads/index.html",
		"Tutorials" => "../Tutorials/index.html",
		"User Manual" => "../User_Manual/index.html",
		"Reference Manual" => "../Reference_Manual/index.html",
		"Developer Manual" => "../Developer_Manual/index.html",
		"Forums" => "../Forums/index.html",
		"Team Members" => "../Team_Members/index.html",
		"Future Work" => "../Future_Work/index.html",
		"FAQ" => "../FAQ/index.html",
		"Links" => "../Links/index.html",
		"Publications" => "../Home/pubs.html",
		);

	# 1. black border (using table)
	print '<table border="0" width="140"><tr><td bgcolor="'.$frame_color.'" valign="top">';
	
	# 2. main menu table
	print '  <table border="0" width="100%" valign="top" cellspacing="3" cellpadding="8">';
		
	# 2.1 menu items
	foreach ($menu_items as $key => $link) {
		if ($link == "Home") {
			$link = "../index.html";
		}
		print '    <tr><td bgcolor="'.$button_color.'"><a target="_top" href="'.$link.'" class="button"><font face="sans-serif"><b>'.$key.'</b></font></a></td></tr>';
	}
	print '  </table>';
	print '</table>
';
}

# Refer and link to a class in a specific module in the Reference Manual
function classref($module,$class) {
  # Epydoc version:
  print "<a target=\"_top\" href=\"../Reference_Manual/$module.$class-class.html\">$class</a>";
  # Pydoc version:
#  print "<a target=\"_top\" href=\"../Reference_Manual/$module.html#$class\">$class</a>";
}

# Refer and link to a function in a specific module in the Reference Manual
function fnref($module,$fn) {
  # Epydoc version:
  print "<a target=\"_top\" href=\"../Reference_Manual/$module-module.html#$fn\">$fn</a>";
}

# Refer and link to a function in a specific module in the Reference Manual
function moduleref($module) {
  # Epydoc version:
  print "<a target=\"_top\" href=\"../Reference_Manual/$module-module.html\">$module</a>";
}
	
?>
