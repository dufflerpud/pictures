#!/usr/bin/perl -w
#
#indx#	app.cgi - An app for creating an index.html for a pile of jpegs and stuff
#@HDR@	$Id$
#@HDR@
#@HDR@	Copyright (c) 2024-2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
#@HDR@
#@HDR@	Permission is hereby granted, free of charge, to any person
#@HDR@	obtaining a copy of this software and associated documentation
#@HDR@	files (the "Software"), to deal in the Software without
#@HDR@	restriction, including without limitation the rights to use,
#@HDR@	copy, modify, merge, publish, distribute, sublicense, and/or
#@HDR@	sell copies of the Software, and to permit persons to whom
#@HDR@	the Software is furnished to do so, subject to the following
#@HDR@	conditions:
#@HDR@	
#@HDR@	The above copyright notice and this permission notice shall be
#@HDR@	included in all copies or substantial portions of the Software.
#@HDR@	
#@HDR@	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
#@HDR@	KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#@HDR@	WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
#@HDR@	AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#@HDR@	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#@HDR@	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#@HDR@	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#@HDR@	OTHER DEALINGS IN THE SOFTWARE.
#
#hist#	2026-02-20 - Christopher.M.Caldwell0@gmail.com - Created
########################################################################
#doc#	app.cgi - An app for creating an index.html for a pile of jpegs and stuff
########################################################################

use strict;
use lib "/usr/local/lib/perl";
use cpi_translate qw(trans xprint);
use cpi_db qw(DBadd DBdel DBget DBpop DBput DBread DBwrite dbarr);
use cpi_file qw(cleanup fatal read_file);
use cpi_compress_integer qw(compress_integer);
use cpi_setup qw(setup);
use cpi_user qw(group_to_name groups_of_user in_group logout_select user_name users_in_group);

&setup( stderr=>"pictures" );

my $EXIF_TMP = "/tmp/exifdata.txt";

#########################################################################
#	Variable declarations.						#
#########################################################################

my $GRAPHICS_BASE=$cpi_vars::BASEFILE;
$GRAPHICS_BASE=~s+/[^/]*$+/albums+g;
my $GRAPHICS_DIR;
my $INDEX;
my @EXTS = ( "htm", "jpg", "jpeg", "pdf", "avi", "mov", "wav", "mp3" );
my %FIELD_TO_EXIFTAG =
    (
    "Where"	=> [ "Location", "Title", "Caption" ],
    "Who"	=> [ "Title", "Caption" ],
    "When"	=> [ "Title", "Caption" ]
    );

my $JAVASCRIPT = "$cpi_vars::BASEDIR/lib/$cpi_vars::PROG.js";

my $unsorted = "";

#########################################################################
#########################################################################
sub make_token
    {
    my( $tokname ) = @_;
    $tokname =~ s/[^\w]+/_/g;
    $tokname =~ s/^_*//;
    $tokname =~ s/_*$//;
    return $tokname;
    }

#########################################################################
#########################################################################
sub dequote
    {
    my( $ret ) = @_;
    return $ret;
    }

#########################################################################
#########################################################################
sub print_slides
    {
    my( $slide, @slides ) = @_;
    my $slidelist = join(',',@slides);
    my $toprint = <<EOF;
<script>
function submit_func( v )
    {
    with( window.document.form )
	{
	func.value = v;
	submit();
	}
    }

function category( cattext )
    {
    var newval=prompt("XL(Enter new possible value for category) '"+cattext+"'","");
    if( newval )
        {
	with( window.document.form )
	    {
	    addcat.value = cattext;
	    addval.value = newval;
	    submit_func( 'addcategory' );
	    }
	}
    add.checked = false;
    }
</script>

<body $cpi_vars::BODY_TAGS>
<form method=post name=form>
<input type=hidden name=func>
<input type=hidden name=addcat>
<input type=hidden name=current_group value="$cpi_vars::FORM{current_group}">
<input type=hidden name=addval>
<input type=hidden name=SID value="$cpi_vars::SID">
<input type=hidden name=returnto value="$cpi_vars::FORM{returnto}">
<input type=hidden name=current_slide value="$slide">
<input type=hidden name=slides value="$slidelist">
<center>
<table border=1 $cpi_vars::TABLE_TAGS>
EOF
    my @fieldlist =
	&DBget( "f", $cpi_vars::FORM{current_group} );
    my $width = scalar(@fieldlist) + 1;
    my $slide_name;
    #foreach $slide_name ( @slides )
    foreach $slide_name ( $slide )
	{
	$toprint .= "<tr><th bgcolor=#c0c0c0 colspan=$width><font color=#007010>$slide_name</font></th></tr>\n";
	$toprint .= "<tr><td rowspan=3 valign=top height=100%>";
	my $url =
	    ( (($slide_name =~ /\.(.*)$/) && grep($1 eq $_,"mov","avi","pdf","html","htm") )
	    ? "click_to_display.jpg"
	    : $slide_name
	    );
	$toprint .= "<a href=albums/$cpi_vars::FORM{current_group}/$slide_name target=picture_tab>";
	#$toprint .= "<embed src=albums/$cpi_vars::FORM{current_group}/$slide_name width=500>";
	$toprint .= "<img src=albums/$cpi_vars::FORM{current_group}/$url width=500>";
	$toprint .= "</a></td>\n";
	my $title;
	foreach $title ( @fieldlist )
	    {
	    $toprint .= "<td valign=top><b>".&trans($title).":</b><br>\n";
	    my $vartok = &make_token( $title );
	    my $varname = "${vartok}_$slide_name";
	    my $val;
	    my %selflag = map { $_, " checked" }
	        split(/,/,&DBget("a",$cpi_vars::FORM{current_group},
		        $slide_name,$vartok) );
	    foreach $val (
		&DBget("l",
		    $cpi_vars::FORM{current_group}, $title ) )
		{
		my $valtok = &make_token( $val );
		$toprint .= "<input name=\"$varname\" value=\"$valtok\" ";
		$toprint .= "type=".&DBget("t",$cpi_vars::FORM{current_group},$title);
		$toprint .= "$selflag{$valtok}>".&trans($val)."<br>\n";
		}
	    $toprint .= "<input type=button value=\"XL(Add an entry)\"";
	    $toprint .= " onClick='category(\"$title\");'>";
	    $toprint .= "</td>\n";
	    }
	$toprint .= "</tr>";
	$toprint .= "<tr><td valign=top colspan=".scalar(@fieldlist).">";
	$toprint .= "XL(When):";
	$toprint .= "<input name=\"When_${slide_name}\" type=text size=10";
	$toprint .= " value=\"".&dequote(
	    &DBget("a",$cpi_vars::FORM{current_group},
	    $slide_name, "When" ) ) . "\">";
	$toprint .= "</td></tr>\n<tr>";
	$toprint .= "<td colspan=".scalar(@fieldlist)." valign=top>";
	$toprint .= "XL(Comments):<br>\n";
	$toprint .= "<textarea name=\"Comments_${slide_name}\" rows=10 cols=40>";
	$toprint .= &dequote( &trans(
	    &DBget( "a", $cpi_vars::FORM{current_group},
	        $slide_name, "Comments" ) ) );
	$toprint .= "</textarea></td></tr>";

	my $href = "$ENV{SCRIPT_NAME}?SID=$cpi_vars::SID&USER=$cpi_vars::USER";
	$toprint .= "<tr><th colspan=$width><table width=100%><tr>";
	$toprint .= "<th align=left><select name=Assigned_$slide_name>";
	my $u;
	$toprint .= "<option value=\"*$cpi_vars::USER\">XL(Mark slide as categorized)";
	foreach $u ( &users_in_group() )
	    {
	    $toprint .= "<option value=$u>XL(Assign slide to) ".
		&user_name( $u )
		if( &in_group( $u, $cpi_vars::FORM{current_group} ) );
	    }
	$toprint .= "</select></th><th align=right>";
	$toprint .= "<select name=myrating_$slide_name>";
	my @peruser = &DBget("a",
	    $cpi_vars::FORM{current_group},$slide_name,"Stati");
	my %sel = ();
	if( $peruser[0] eq "*" )
	    { $sel{2} = " selected"; }
	elsif( grep($_ eq $cpi_vars::USER,@peruser) )
	    { $sel{1} = " selected"; }
	else
	    { $sel{0} = " selected"; }
	$toprint .= "<option$sel{0} value=0>Good slide";
	$toprint .= "<option$sel{1} value=1>I never need to see this again";
	$toprint .= "<option$sel{2} value=2>Nobody will be interested";
	$toprint .= "<option value=3>Throw this away";
	$toprint .= "</select></th></tr>";
	}
    $toprint .= "<tr><th colspan=1 align=left>";
    $toprint .= "<input type=button onClick='submit_func(\"Previous\");' value='&larr;')>";
    $toprint .= "<input type=button onClick='submit_func(\"Update\");' value=XL(Update)>";
    $toprint .= "<input type=button onClick='submit_func(\"Next\");' value='&rarr;'>";
    $toprint .= "</th><th align=right>$unsorted</th></tr>";
    $toprint .= "</table></th></tr></table></center></form>";
    &xprint( $toprint );
    }

#########################################################################
#	Print a footer.							#
#########################################################################
sub footer
    {
    my @toprint = ( <<EOF );
<script>
function subfunc( fnc )
    {
    with( window.document.footerform )
        {
	footerfunc.value = fnc;
	submit();
	}
    }
</script>
<form name=footerform method=POST ENCTYPE="multipart/form-data">
<input type=hidden name=footerfunc>
<input type=hidden name=SID value="$cpi_vars::SID">
<center><table $cpi_vars::TABLE_TAGS width=80% border=1>
<tr><th><table width=100%><tr>
<td align=left><input type=file name=newfile>
<input type=button onClick='subfunc("upload");' value="XL(Upload file)">
</td>\n<td align=right>
<select name=current_group onChange='subfunc(\"home\");'>
EOF
    my $g;
    my %selflag = ( $cpi_vars::FORM{current_group}, " selected" );
    foreach my $fg (&groups_of_user($cpi_vars::USER))
        {
	next if( $fg !~ /pictures_(.*)$/ );
	my $g = $1;
	my $fullname = &group_to_name($fg);
	$fullname =~ s/pictures\s*//gi;
	push(@toprint, "<option value=$g$selflag{$g}>", $fullname)
	    if( -d "$GRAPHICS_BASE/$1" );
	}
    push( @toprint,
        "</select>\n<input type=button onClick='subfunc(\"home\");'",
        " value=\"XL(Home)\">\n",
        "<input type=button ",
        "onClick='window.location=\"albums/$cpi_vars::FORM{current_group}\";'",
        " value=\"XL(Sorted slides)\">\n",
        "<input type=button onClick='subfunc(\"generate\");'",
        " value=\"XL(Generate slides)\">\n",
        "<input type=button onClick='subfunc(\"statistics\");'",
        " value=\"XL(Statistics)\">\n",
        "<input type=button onClick='subfunc(\"admin\");'",
        " value=\"XL(Administration)\">\n",
        &logout_select("footerform"),
        "</td></tr></table></th></tr></table></center></form>");
    &xprint(@toprint);
    }

#########################################################################
sub print_statistics
    {
    my $toprint = <<CEOF;
<body $cpi_vars::BODY_TAGS><center><table $cpi_vars::TABLE_TAGS border=1>
<tr><th align=left>XL(Who)</th><th>XL(Assigned)</th><th>XL(Categorized)</th></tr>
CEOF
    my %doneby = ();
    my %assignedto = ();
    my $t_assigned = 0;
    my $t_categorized = 0;
    #my $t_untouched = 0;
    my $total = 0;
    my $s;
    foreach $s ( &get_slide_list() )
        {
	$_ = &DBget("a",$cpi_vars::FORM{current_group},
	    $s, "Assigned" );
	if( $_ eq "" )
	    {
	    #$t_untouched++;
	    }
	elsif( /\*(.*)/ )
	    {
	    $doneby{$1}++;
	    $t_categorized++;
	    }
	else
	    {
	    $assignedto{$_}++;
	    $t_assigned++;
	    }
	$total++;
	}
    my $t_untouched = $total - $t_assigned - $t_categorized;
    my $u;
    my %uhash = ();
    foreach $u ( &users_in_group() )
        {
	$uhash{$u}++ if( &in_group( $u, $cpi_vars::FORM{current_group} ) );
	}
    grep( $uhash{$_}++, keys %doneby );
    grep( $uhash{$_}++, keys %assignedto );
    foreach $u ( sort keys %uhash )
	{
	$_ = &user_name($u);
	$toprint .= "<tr><th align=left>${_}:</th>" .
	    "<td align=right>".($assignedto{$u}+0).
	    "</td>\n<td align=right>".($doneby{$u}+0)."</td></tr>";
	}

    $toprint .= <<CEOF;
<tr><th colspan=3></th></tr>
<tr><th align=left>Total:</th><td align=right>$t_assigned</td>
    <td align=right>$t_categorized</td></tr>
<tr><th align=left>XL(Total untouched):</th>
    <td align=right colspan=2>$t_untouched</td></tr>
<tr><th align=left>XL(Total slides in album):</th>
    <td align=right colspan=2>$total</td></tr>
</table></center>
CEOF
    &xprint($toprint);
    }

#########################################################################
#	Get a list of all possible slides.				#
#########################################################################
sub get_slide_list
    {
    my @res;
    opendir(D,$GRAPHICS_DIR)||&fatal("Cannot open $GRAPHICS_DIR:  $!");
    while( my $fn = readdir(D) )
	{
	next if( $fn eq "click_to_display.jpg" );
	next if( $fn !~ /\.([^\.]+)$/);
	push(@res,$fn) if( grep( $1 eq $_, @EXTS ) );
	}
    closedir(D);
    return @res;
    }

#########################################################################
#	Find an unsorted slide.						#
#########################################################################
sub unsorted_slides()
    {
    my @ret;
    &DBwrite( );
    foreach my $slide_name ( &get_slide_list() )
	{
	my $assignee = &DBget("a",
	    $cpi_vars::FORM{current_group}, $slide_name, "Assigned");
	if( !$assignee || ($assignee eq $cpi_vars::USER) )
	    {
	    my $when = &DBget("a",
		$cpi_vars::FORM{current_group}, $slide_name, "When");
	    if( ! $when )
	        { push( @ret, $slide_name ); }
	    else
	        {
		&DBput("a",
	    	    $cpi_vars::FORM{current_group}, $slide_name, "Assigned",
		    "*chris" );
		&xprint("Fixing $slide_name<br>\n");
		}
	    }
	}
    $unsorted = scalar(@ret) . " left unsorted";
    &DBpop( );
    return @ret;
    }

#########################################################################
#	Simple file locking using symbolic links.			#
#########################################################################
sub clear_lock { unlink( "$_[0].lock" ); }
sub set_lock
    {
    while( ! symlink( $$, "$_[0].lock" ) )
        { sleep(1); }
    }

#########################################################################
#	OUT is open to log file on return.				#
#########################################################################
sub open_log
    {
    my $fn = "$GRAPHICS_DIR/log.html";
    if( -f $fn )
        {
	open( OUT, ">> $fn" ) || &fatal("Cannot append to ${fn}:  $!");
	}
    else
	{
	open( OUT, "> $fn" ) || &fatal("Cannot write ${fn}:  $!");
	print OUT "<body $cpi_vars::BODY_TAGS><center>";
	print OUT "<table border=1 cellspacing=0 cellpadding=0 $cpi_vars::TABLE_TAGS>\n";
	print OUT "<tr><th>When</th><th>Slide</th><th>User</th><th>Assigned</th>";
	my @fieldlist =
            &DBget( "f", $cpi_vars::FORM{current_group} );
	foreach $_ ( @fieldlist )
	    { print OUT "<th>$_</th>"; }
	print OUT "<th>Comments</th></tr>\n";
	}
    }

#########################################################################
#########################################################################
sub update_slides
    {
    my($sec,$min,$hour,$mday,$month,$year) = localtime(time);
    my $now = sprintf("%02d/%02d/%04d %02d:%02d",
        $mday,$month+1,$year+1900,$hour,$min);

    my %slide_comments;
    my $slidename;
    my $entry;

    my @slides_to_update =
	split(/,/, $cpi_vars::FORM{slides} || $cpi_vars::FORM{current_slide} );

    foreach $slidename ( @slides_to_update )
        {
	$slide_comments{$slidename} =
	    &trans(
	        &DBget("a",
		    $cpi_vars::FORM{current_group},
		    $slidename, "Comments" ) );
	}
    my @fieldlist =
	&DBget( "f", $cpi_vars::FORM{current_group} );
    my $logentries = "";
    &DBwrite( );
    foreach $slidename ( @slides_to_update )
	{
	$logentries .= "<tr><td>$now</td>\n";
	$logentries .= "<td><a href=../../pictures.cgi?slide=$slidename&current_group=$cpi_vars::FORM{current_group}>$slidename</a></td>\n";
	$logentries .= "<td>$cpi_vars::USER</td>\n";
	$logentries .= "<td>$cpi_vars::FORM{assigned}</td>\n";
	foreach $entry ( @fieldlist )
	    {
	    my $varname = &make_token( $entry );
	    my $val =  $cpi_vars::FORM{"${varname}_${slidename}"};
	    &DBput( "a", $cpi_vars::FORM{current_group},
	        $slidename, $varname, $val );
	    $val = "&nbsp;" if( $val eq "" );
	    $logentries .= "<td>$val</td>\n";
	    }
	my $fc = $cpi_vars::FORM{"Comments_$slidename"};
	$logentries .= "<td><pre>$fc</pre></td></tr>\n";
	$fc =~ s/"/'/g;
	&DBput( "a", $cpi_vars::FORM{current_group},
	    $slidename, "Comments", "$cpi_vars::LANG|$fc" )
	    if( $fc ne $slide_comments{$slidename} );
	&DBput( "a", $cpi_vars::FORM{current_group},
	    $slidename, "When", $cpi_vars::FORM{"When_$slidename"} );
	&DBput( "a", $cpi_vars::FORM{current_group},
	    $slidename, "Assigned", $cpi_vars::FORM{"Assigned_$slidename"} );
	my $myrating = $cpi_vars::FORM{"myrating_$slidename"};
	if( $myrating eq "0" )
	    {
	    &DBdel("a",$cpi_vars::FORM{current_group},
		$slidename, "Stati", $cpi_vars::USER );
	    }
	elsif( $myrating eq "1" )
	    {
	    &DBadd("a",$cpi_vars::FORM{current_group},
		$slidename, "Stati", $cpi_vars::USER );
	    }
	elsif( $myrating eq "2" || $myrating eq "3" )
	    {
	    &DBput("a",$cpi_vars::FORM{current_group},
		$slidename, "Stati", "*" );
	    rename( "$GRAPHICS_DIR/$slidename", "$GRAPHICS_DIR/$slidename.del" )
		if( $myrating eq "3" );
	    }
	}
    &DBpop( );
    &make_javascript();
    &open_log();
    print OUT $logentries;
    close( OUT );
    }

#########################################################################
#########################################################################
sub addcat
    {
    my( $catname, $catval ) = @_;
    &DBwrite( );
    &DBadd( "l", $cpi_vars::FORM{current_group},
        $catname, $catval );
    &DBpop( );
    }

#########################################################################
#########################################################################
sub add_slide
    {
    my $new_slide_name = &compress_integer(time());		# Ick
    my $filename = "$GRAPHICS_DIR/$new_slide_name";
    &write_file( "$filename.noext", $cpi_vars::FORM{newfile} );

    $_ = &read_file( "file $filename.noext |" );

    my $ext;
    if( /JPEG image/ )
        { $ext = ".jpg"; }
    elsif( /PDF document/ )
        { $ext = ".pdf"; }
    elsif( /RIFF.*AVI/ )
        { $ext = ".avi"; }
    elsif( /Apple QuickTime/ )
        { $ext = ".mov"; }

    if( $ext )
        {
	&fatal("Cannot rename $filename.noext to $filename.ext:  $!")
	    unless( rename( "$filename.noext", "$filename.$ext" ) );
	$new_slide_name = "$new_slide_name.$ext";
	}

    my($sec,$min,$hour,$mday,$month,$year) = localtime(time);
    my $now = sprintf("%02d/%02d/%04d %02d:%02d",
        $mday,$month+1,$year+1900,$hour,$min);
    my @fieldlist =
	&DBget( "f", $cpi_vars::FORM{current_group} );
    my $width = scalar(@fieldlist) + 2;
    &open_log();
    print OUT "<tr><td>$now</td><td><a href=../../pictures.cgi?slide=$new_slide_name&current_group=$cpi_vars::FORM{current_group}>$new_slide_name</a></td><td>$cpi_vars::USER</td><td colspan=$width>Uploaded</td></tr>\n";
    close( OUT );
    $cpi_vars::FORM{current_slide} = $new_slide_name;
    }

#########################################################################
#########################################################################
sub date_of
    {
    my( $slide ) = @_;
    my $when = &DBget( "a", $cpi_vars::FORM{current_group}, $slide, "When" );
    return 0 if( !defined($when) || $when eq "" );
    $when =~ s/\~//g;
    my @dtoks = split(/\//,$when);
    return sprintf("%04d/%02d/%02d",$dtoks[0],0,0) 			if( scalar(@dtoks) == 1 );
    return sprintf("%04d/%02d/%02d",$dtoks[1],$dtoks[0],0)		if( scalar(@dtoks) == 2 );
    return sprintf("%04d/%02d/%02d",$dtoks[2],$dtoks[0],$dtoks[1])	if( scalar(@dtoks) == 3 );
    }

#########################################################################
#########################################################################
sub make_javascript
    {
    #return 1;	#CMC
    $| = 1;
    #my $toprint = "<!doctype html><html lang=en><HEAD>" . &read_file( $JAVASCRIPT );
    my $toprint = "<html lang=en><HEAD>" . &read_file( $JAVASCRIPT );
    my $slidetext = "";
    my $slide;
    my $fi;
    my @fieldlist = &DBget("f",
        $cpi_vars::FORM{current_group} );
    my @ulist = ();
    my $u;
    foreach $u ( &users_in_group() )
        {
	push( @ulist, $u ) if( &in_group( $u, $cpi_vars::FORM{current_group} ) );
	}
    foreach $slide ( sort { &date_of($a) cmp &date_of($b) } &get_slide_list() )
        {
	$_ = &DBget("a",$cpi_vars::FORM{current_group},
            $slide, "Stati" );
	next if( $_ && ( $_ eq "chris" || $_ eq "*" ) );
	$slidetext .= "," if( $slidetext );
	my $when = &DBget("a",$cpi_vars::FORM{current_group},
	    $slide, "When" );
	$_ = &DBget("a",$cpi_vars::FORM{current_group},
	    $slide, "Comments" );
	s/[\r]+//gs;
	s/^[a-z][a-z]\|//gs;
	if( /\n/ )
	    {
	    s/\n/\\n/gs;
	    $_ = "<pre>$_</pre>";
	    }
	s/(")/\\$1/g;
	if( $when && $when ne "UNKNOWN" )
	    {
	    $slidetext .= "\n{ n:\"$slide\",c:\"$_<br>($when)\",w:\"$when\",f:{";
	    }
	else
	    {
	    $slidetext .= "\n{ n:\"$slide\",c:\"$_\",f:{";
	    }
	for( $fi=0; $fi<scalar(@fieldlist); $fi++ )
	    {
	    $slidetext .= ", " if( $fi > 0 );
	    my @l = ();
	    my $fiv = &make_token($fieldlist[$fi]);
	    my $oi;
	    my @vals = &DBget("l",
	        $cpi_vars::FORM{current_group},$fieldlist[$fi]);
	    for( $oi=0; $oi<scalar(@vals); $oi++ )
	        {
		my $l4 = &make_token($vals[$oi]);
		my $lh;
		foreach $lh ( split(/,/,
		    &DBget( "a",
			$cpi_vars::FORM{current_group}, $slide, $fiv ) ) )
		    {
		    if( $l4 eq $lh )
		        {
			push( @l, "${oi}:1" );
			last;
			}
		    }
		}
	    $slidetext .= "$fi:{".join(",",@l)."}";
	    }
	$slidetext .= "},u:{";
	my @stati = &DBget("a",$cpi_vars::FORM{current_group},
	    $slide, "Stati" );
	my $ui = 0;
	my $seenusers = 0;
	for( $ui=0; $ui<scalar(@ulist); $ui++ )
	    {
	    $u = $ulist[$ui];
	    if( $stati[0] eq "*" || grep($_ eq $u,@stati) )
	        {
		$slidetext .= "," if( $seenusers++ );
		$slidetext .= "${ui}:1";
		}
	    }
	$slidetext .= "}}";
	}
    $toprint =~ s/%%SLIDES%%/$slidetext/gs;
    $toprint =~ s/%%CURRENT_GROUP%%/$cpi_vars::FORM{current_group}/gs;
    my $nametext = "";
    my $p;
    my $extsep = "";
    foreach $p ( @fieldlist )
        {
	$nametext .= "${extsep}" . "{ t:\"$p\", v:[";
	$extsep = ",";
	my $intsep = "";
	foreach $_ ( &DBget("l",
			$cpi_vars::FORM{current_group},$p) )
	    {
	    $nametext .= "$intsep\"$_\"";
	    $intsep = ",";
	    }
	$nametext .= "]}";
	}
    $toprint =~ s/%%CATEGORYNAMES%%/$nametext/gs;
    $toprint .= <<EOF;
<style>
\@media screen and (max-width:1024px) {
    .bigscreen {
        display:none;
    }
}
</style>
<meta name="apple-mobile-web-app-capable" content="yes">
EOF
    $toprint .= "</HEAD><BODY $cpi_vars::BODY_TAGS><form name=form>";
    $toprint .= "<center><table $cpi_vars::TABLE_TAGS width=95% border=1>";
    $toprint .= "<tr><td rowspan=2 valign=top>";
    $toprint .= "<table width=100%><tr>";
    $toprint .= "<td width=100% colspan=3><table width=100%><tr><td align=left valign=top>";
    $toprint .= "<input type=button value=\"&lt;&lt;\" id=prevbut onClick='next_slide(-1,-1);'>";
    $toprint .= "<input type=button value=\"&lt;\" style='background-Color:#d0d0d0' onClick='next_slide(-1,0);'>";
    $toprint .= "</td><td align=center>";
    $toprint .= "<div id=where_picture>TEXT</div></td><td align=right valign=top>";
    $toprint .= "<input type=button value=\"&gt;\" style='background-Color:#d0d0d0' onClick='next_slide(1,0);'>";
    $toprint .= "<input type=button value=\"&gt;&gt;\" id=nextbut onClick='next_slide(1,1);'>";
    $toprint .= "</td></tr></table></td></tr>";
    $toprint .= "<tr><td valign=top align=left><div id=upperleft></div></td>";
    $toprint .= "<td width=100%><center>";
    $toprint .= "<a target=picture_tab name=picture_url id=picture_url>";
    #$toprint .= "<embed onLoad='picture_loaded();' width=1 id=current_picture name=current_picture alt='Click to display'>";
    $toprint .= "<img border=10px style='border:10px' onLoad='picture_loaded();' width=1 id=current_picture name=current_picture alt='Click to display'>";
    $toprint .= "</a><br><input type=button value=\"Random\" id=randombut onClick='next_slide(0,1);'></center><br>";
    $toprint .= "<div id=details>FRED</div><div id=detailsend></div></td>";
    $toprint .= "<td align=right valign=top><div id=upperright></div></td></tr>";
    $toprint .= "</table></td>";
    for( $fi=0; $fi<scalar(@fieldlist); $fi++ )
	{
	my $title = $fieldlist[$fi];
	$toprint .= "<td class=bigscreen width=1% nowrap valign=top><b>".&trans($title).":</b><br>";
	my $vartok = &make_token( $title );
	my $vali;
	my $val;
	my @vals = &DBget("l",
	    $cpi_vars::FORM{current_group},$title);
	for( $vali=0; $vali<scalar(@vals); $vali++ )
	    {
	    my $val = $vals[$vali];
	    my $ext = "_${fi}_${vali}";
	    $toprint .= "<div id=id$ext>";
	    $toprint .= "<input name=\"cb$ext\" type=checkbox";
	    $toprint .= " onClick='get_slide();'>";
	    $toprint .= &trans($val)."</div>";
	    }
	$toprint .= "</td>";
	}
    $toprint .= "</tr>";
    $toprint .= "<tr><td class=bigscreen colspan=$fi>Search for:";
    $toprint .= "<input type=text name=search4>";
    $toprint .= "<input type=button value=Search onClick='get_slide();'>";
    $toprint .= "</td></tr></table></form></center><div id=debuginfo></div>\n";
    $toprint .= "<script>get_slide();</script>\n";
    $toprint .= "</BODY></HTML>\n";
    open( OUT, "> $INDEX" ) || &fatal("Cannot write $INDEX:  $!");
    print OUT $toprint;
    close( OUT );
    }

#########################################################################
#########################################################################
sub add_text_to_images
    {
    my( $album ) = @_;
    $GRAPHICS_DIR="$GRAPHICS_BASE/$album";
    print "Database:            $cpi_vars::DB\n";
    print "Graphics Directory:  $GRAPHICS_DIR\n";
    &DBread( );
    foreach my $slide ( sort {&date_of($a) cmp &date_of($b)} &get_slide_list() )
        {
	if( $slide !~ /\.jpg$/ )
	    {
	    print "Do not know how to fix slide $slide.\n";
	    next;
	    }

	my @txts = ( sprintf("%-11s%s","Slide:",$slide) );
	my %exifargs = ();

	foreach my $fld
	    ("Where","Who","Why","When","Assigned","Stati","Comments")
	    {
	    my $val = &DBget("a",$album,$slide,$fld);
	    next if( ! $val );
	    push( @txts, sprintf("%-11s%s",${fld}.":",$val) );
	    grep( push( @{$exifargs{$_}}, $val ),
		sort @{$FIELD_TO_EXIFTAG{$fld}} )
		if( $FIELD_TO_EXIFTAG{$fld} );
	    }

	$_ = join("\n ","",@txts)."\n";
	push( @{ $exifargs{Description}		}, $_ );
	push( @{ $exifargs{Comment}		}, $_ );
	push( @{ $exifargs{ImageDescription}	}, $_ );

	my $fn = "$GRAPHICS_DIR/$slide";
	my $nfn = "$fn.new";
	$_ = "rdjpgcom $fn";
	open( INF, "$_ |" ) || die("Cannot '$_':  $!");
	$_ = <INF>;
	close( INF );

	if( 0 && defined($_) && $_ =~ /e/ )
	    { print STDERR "Skipping $fn.\n"; }
	else
	    {
	    $_ = "wrjpgcom -r $fn > $nfn";
	    open( OUT, "| $_" ) || die("Cannot '$_':  $!");
	    print OUT join("\n",@txts),"\n";
	    close( OUT );

	    my @exif_array = ("exiftool");
	    foreach my $fld ( keys %exifargs )
		{
		push(@exif_array, "-$fld='".join(" ",@{$exifargs{$fld}})."'");
		}
	    push( @exif_array, $nfn );

	    my $exiftool_cmd = join(" ",@exif_array);
	    print "+ $exiftool_cmd\n";
	    system( $exiftool_cmd );
	    if( ! -f $nfn )
	        { print "$_ did not create a file.\n"; }
	    elsif( (-s $nfn) < (-s $fn) )
	        {
		print "$_ left ",
		    ( ( -s $nfn ) ? "small/truncated" : "empty" ),
		    "file (deleted).\n";
		unlink $nfn;
		}
	    else
		{
		rename($nfn,$fn) || die("Cannot rename $nfn to $fn:  $!");
		print "$fn updated.\n";
		}
	    }
	}
    &cleanup(0);
    }

#########################################################################
#	Make filenames for a slide.					#
#########################################################################
sub generate_links
    {
    my( $album, $dir ) = @_;
    $GRAPHICS_DIR="$GRAPHICS_BASE/$album";
    &DBread();
    my %dest_filenames = ();
    foreach my $slide ( sort {&date_of($a) cmp &date_of($b)} &get_slide_list() )
        {
	my @toks;
	#print "# $slide";
	foreach my $fld ("Where","Who","When","Comments")
	    {
	    #print " $album/$slide/$fld=";
	    $_ = &DBget("a",$album,$slide,$fld);
	    if( ! defined($_) || $_ eq "" )
		{
		#print "(empty)";
		next;
		}
	    #print "[$_]";
	    s/^en\|//i;
	    s/'s/s/gms;
	    s/,/ and /gms if( $fld eq "Who" );
	    s/[^a-zA-Z0-9]+/_/gms;
	    s/_and_/\+/gms;
	    $_ = $1 if( /^_*(.*?)_*$/ );
	    #print " or [$_]";
	    push( @toks, $_ );
	    }
	my $base = sprintf("%.200s",join("-",@toks));
	#print " becomes [$base]\n";

	#print "[$slide] to [$base]\n";
	push( @{$dest_filenames{$base}}, $slide );
	}
    &DBpop();

    &DBwrite();
    foreach my $fn ( sort keys %dest_filenames )
	{
	my $ext = ( $dest_filenames{$fn}[0] =~ /^(.*)\.(\w+?)$/ ? $2 : "" );
	if ( scalar( @{$dest_filenames{$fn}} ) == 1 )
	    {
	    my $ndfn = "$fn.$ext";
	    print "cp $GRAPHICS_DIR/$dest_filenames{$fn}[0] $dir/$ndfn\n";
	    &DBput("a",$album,$dest_filenames{$fn}[0],"fn",$ndfn);
	    }
	else
	    {
	    my $ind = 0;
	    foreach my $dfn ( @{$dest_filenames{$fn}} )
	        {
		my $ndfn = sprintf("$fn,%02d.$ext\n",$ind++);
		printf("cp $GRAPHICS_DIR/$dfn $dir/$ndfn");
	        &DBput("a",$album,$dfn,"fn",$ndfn);
		}
	    }
#       &fatal("Cannot link $GRAPHICS_DIR/$slide to $_:  $!")
#	    if( ! link( "$GRAPHICS_DIR/$slide", $_ ) );
	}
    &DBpop();
    &cleanup(0);
    }

#########################################################################
#	Add database entries to text field of all jpegs.		#
#########################################################################
sub directory_structure
    {
    my( $album ) = @_;
    $GRAPHICS_DIR="$GRAPHICS_BASE/$album";
    my $LINKS_DIR="$GRAPHICS_DIR/../links";
    print "Database:            $cpi_vars::DB\n";
    print "Graphics Directory:  $GRAPHICS_DIR\n";
    print "Link directory:      $LINKS_DIR\n";
    system("rm -rf $LINKS_DIR; mkdir -p $LINKS_DIR");
    &DBread( );
    my %files_in_dir = ();
    my %slide_to_title = ();
    my %title_to_slide = ();
    foreach my $slide ( sort {&date_of($a) cmp &date_of($b)} &get_slide_list() )
        {
	$_ = &DBget("a",$album,$slide,"When");
	s+~++;
	if( m:(\d+)/(\d+)/(\d+): )
	    { $_ = sprintf("%04d%02d%02d",$3,$1,$2); }
	elsif( m:(\d+)/(\d+): )
	    { $_ = sprintf("%04d%02d",$2,$1); }

	my( @attrs ) = ( $_ );
	
	foreach my $fld ("Where","Who","Why")
	    {
	    my $value_list = &DBget("a",$album,$slide,$fld);
	    next if( !defined($value_list) || $value_list eq "" );
	    foreach my $value ( split(/,/,$value_list) )
	        {
		push( @{$files_in_dir{"$fld/$value"}}, $slide );
		push( @attrs, $value );
		}
	    }

	$_ = &DBget("a",$album,$slide,"Comments");
	s/'s/s/gs;
	s/[^\w]+/_/gs;
	s/^_*//;
	s/_*$//;
	push( @attrs, $_ );

	my $title_base = join("_",@attrs);
	$title_base =~ s/_en_/_/g;
	$title_base = substr( $title_base, 0, 200 );
	my $ind = 1;
	my $title = $title_base;
	while( defined($title_to_slide{$title}) )
	    {
	    $title = sprintf("%s_%03d",$title_base,$ind++);
	    }
	$title_to_slide{$title} = $slide;
	$slide_to_title{$slide} = $title;
	}
    chdir( $LINKS_DIR ) || &fatal("Cannot chdir ${LINKS_DIR}:  $!");
    system("mkdir -p " . join(" ",sort keys %files_in_dir));
    foreach my $dir ( sort keys %files_in_dir )
        {
	foreach my $slide ( @{ $files_in_dir{$dir} } )
	    {
	    my $ext = $slide;
	    $ext =~ s+.*\.++;
	    my $fn = "$slide_to_title{$slide}.$ext";

	    symlink( "../../../media/$slide", "$dir/$fn" ) ||
#	    link( "$GRAPHICS_DIR/$slide", "$dir/$fn" ) ||
	        &fatal(
		    "Cannot link $dir/$fn to $GRAPHICS_DIR/$slide:  $!");
	    }
	}
    &cleanup(0);
    }

#########################################################################
#########################################################################
#sub convert_hashes
#    {
#    my( $album ) = @_;
#    my( $slide, $attr );
#    print "Convert_hashes running...\n";
#    &DBwrite( );
#    foreach $slide ( keys %slides )
#        {
#	print "Converting slide $slide.\n";
#	foreach $attr ( keys %{$slides{$slide}} )
#	    {
#	    my $val = $slides{$slide}{$attr};
#	    &DBput( "a", $album, $slide, $attr, $val )
#	        if( $val ne "" );
#	    }
#	}
#    my( $pf );
#    my @title_list = ();
#    foreach $pf ( @picfields )
#        {
#	my $tn = ${$pf}{title};
#	print "Converting field $tn.\n";
#	push( @title_list, $tn );
#	&DBput( "t", $album, $tn, ${$pf}{type} );
#	&DBput( "l", $album, $tn,
#	    &dbarr( @{${$pf}{list}} ) );
#	}
#    &DBput( "f", $album, &dbarr( @title_list ) );
#    &DBpop( );
#    exit(0);
#    }

#########################################################################
#########################################################################
sub usage
    {
    &fatal( @_,
	"XL(Usage):  $cpi_vars::PROG.cgi (dump|dumpaccounts|dumptranslations|undump|undumpaccounts|undumptranslations) [ dumpname ]");
    }

#########################################################################
#	Mainline							#
#########################################################################
#if( $cpi_vars::FORM{footerfunc} eq "admin"
# || $cpi_vars::FORM{modrequest} )
#    { &admin_page(); }

if( ! $ENV{SCRIPT_NAME} )
    {
    &usage("No argument specified.")		if( ! @ARGV );
    &convert_hashes( $ARGV[1] )			if( $ARGV[0] eq "convert" );
    &add_text_to_images( $ARGV[1] )		if( $ARGV[0] eq "add_text_to_images" );
    &generate_links( $ARGV[1], $ARGV[2] )	if( $ARGV[0] eq "generate_links" );
    &directory_structure( $ARGV[1] )		if( $ARGV[0] eq "directory_structure" );
    &fatal("Unknown function [$ARGV[0]]");
    }

#print map( "FORM{$_} = [$cpi_vars::FORM{$_}]<br>\n", keys %cpi_vars::FORM );

my $bestg;
foreach my $admin_group ( &groups_of_user( $cpi_vars::USER ) )
    {
    print STDERR "Checking $cpi_vars::USER against $admin_group.\n";
    next if( $admin_group !~ /^pictures_(.*)$/ );
    my $g = $1;
    print STDERR "g=[$g]\n";
    print STDERR "Checking $GRAPHICS_BASE/$g.\n";

    if( -d "$GRAPHICS_BASE/$g" )
        {
	$bestg = $g;
	last if( $g eq $cpi_vars::FORM{current_group} );
	}
    }
print STDERR "End loop.\n";
if( $bestg )
    { $cpi_vars::FORM{current_group} = $bestg; }
else
    { &fatal("No group appropriate for $cpi_vars::USER"); }

$GRAPHICS_DIR = "$GRAPHICS_BASE/$cpi_vars::FORM{current_group}";
$INDEX = "$GRAPHICS_DIR/index.html";

if( $cpi_vars::FORM{addcat} )
    { &addcat( $cpi_vars::FORM{addcat}, $cpi_vars::FORM{addval} ); }
elsif( $cpi_vars::FORM{newfile} )
    {
    &add_slide();
    &update_slides();
    }
elsif( $cpi_vars::FORM{slides} )
    {
    if( $cpi_vars::FORM{returnto} eq "sorted" )
        {
	&xprint("<h3>Updating database and returning to slide show <blink>...</blink></h3>");
	}
    if( $cpi_vars::FORM{func} eq "Previous" 
	|| $cpi_vars::FORM{func} eq "Update"
	|| $cpi_vars::FORM{func} eq "Next" )
	{
	my @slides = &unsorted_slides();
	my $offset = 0;
	if( $cpi_vars::FORM{func} eq "Update" )
	    {
	    my( $slide_was_at ) =
		grep($slides[$_] eq $cpi_vars::FORM{current_slide}, 0..$#slides);
	    &xprint("<h3>UPDATE SLIDES</h3>");
	    &update_slides();
	    @slides = &unsorted_slides();
	    $cpi_vars::FORM{current_slide} = $cpi_vars::FORM{slide} =
		$slides[$slide_was_at] || $slides[$slide_was_at-1];
	    $offset = 0;
	    }
	elsif( $cpi_vars::FORM{func} eq "Previous" )
	    { $offset = -1; }
	elsif( $cpi_vars::FORM{func} eq "Next" )
	    { $offset = 1; }
	else
	    { &fatal("$cpi_vars::FORM{func} inappropriate at %d",__LINE__); }
	$cpi_vars::FORM{current_slide} = $cpi_vars::FORM{slide}
	    if($cpi_vars::FORM{slide});

#	&xprint( join("",
#	    "func=$cpi_vars::FORM{func}",
#	    " current_slide=",($cpi_vars::FORM{current_slide}||"UNDEF")
#	    ,"<br>slides=",join(",",@slides),"<br>\n"
#	    ) );
	if( @slides )
	    {
	    my( $i ) =
		grep($slides[$_] eq $cpi_vars::FORM{current_slide}, 0..$#slides);
	    if( ! defined( $i ) )
		{ &xprint("<h2>Could not find slide $cpi_vars::FORM{func} to $cpi_vars::FORM{current_slide}</h2>\n"); }
	    elsif( ! defined( $slides[$i + $offset ] ) )
		{ &xprint("<h2>Could not find slide $cpi_vars::FORM{func} to $cpi_vars::FORM{current_slide}=$i</h2>\n"); }
	    else
	        {
		$i += $offset;
		$cpi_vars::FORM{current_slide} = $slides[$i];
		#&xprint("<br>offset=$offset i=$i new slide = $cpi_vars::FORM{current_slide}\n");
		}
	    }
	}
    if( $cpi_vars::FORM{returnto} eq "sorted" )
	{
	&xprint("<meta http-equiv=\"refresh\" content=\"0;url=albums/$cpi_vars::FORM{current_group}\" />\n");
	&cleanup(0);
	}
    }
elsif( $cpi_vars::FORM{func} eq "Update" )
    {
    &update_slides();
    print "Updated.<br>\n";
    &cleanup(0);
    }
elsif( $cpi_vars::FORM{footerfunc} eq "generate" )
    { &make_javascript(); }

if( $cpi_vars::FORM{footerfunc} eq "statistics" )
    { &print_statistics(); }
else
    {
    my @slides = &unsorted_slides();
    if( $cpi_vars::FORM{slide} )
        { &print_slides( $cpi_vars::FORM{slide}, @slides ); }
    elsif( ! @slides )
	{
	&xprint("<h1>XL(All slides are sorted)</h1>\n");
	}
    else
	{
	$cpi_vars::FORM{current_slide} ||= $slides[0];
	&print_slides( $cpi_vars::FORM{current_slide}, @slides );
	}
    }
&footer();
&cleanup(0);
