<HTML><HEAD>
<META HTTP-EQUIV="content-type" CONTENT="text/html; charset=ISO-8859-1">
<LINK rel="stylesheet" type="text/css" media="screen" href="../shared/topo.css">
<TITLE>The Topographica Neural Map Simulator</TITLE>
</HEAD>
<?php

	include('../shared/config.php');

	# Hack: expects name of textfile to be passed in through the
	# arbitrary php.ini option 'sendmail_from'.
	$textfile = ini_get('sendmail_from');
        global $textfile;

        global $body_bg_color;
	print '<BODY bgcolor="'.$body_bg_color.'">';

	# 1. load the utility routines
        require_once('../shared/util.php');

	# 2. get current folder name
        $fname = folder_name();

	# 3. generate the banner

	print "<blockquote>\n";

	banner($fname);

	# 4. news box, if needed
	if ($fname == "/Home" && $textfile == "index_text.php")
           include('../Home/news_text.php');

	# 5. main text
	print '<table border="0" cellpadding="10" width="100%"><tr><td valign="top" bgcolor="'.$menu_bg_color.'" width="145">';

	# 5.2 menu column (right)
	menu_side($fname);

	# separator
	print '</td><td valign="top" bgcolor="'.$banner_bg_color.'">';
	
	# 5.1 main text column (left)
	include('..'.$fname.'/'.$textfile);

	# close table
	print '</td></tr></table>';

	# 6. trailer
	include('../shared/trailer.php');

?>

</BODY>
</HTML>
