<script>
//indx#	pictures.js - Javascript embedded in index.html with pictures
//@HDR@	$Id$
//@HDR@
//@HDR@	Copyright (c) 2024-2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
//@HDR@
//@HDR@	Permission is hereby granted, free of charge, to any person
//@HDR@	obtaining a copy of this software and associated documentation
//@HDR@	files (the "Software"), to deal in the Software without
//@HDR@	restriction, including without limitation the rights to use,
//@HDR@	copy, modify, merge, publish, distribute, sublicense, and/or
//@HDR@	sell copies of the Software, and to permit persons to whom
//@HDR@	the Software is furnished to do so, subject to the following
//@HDR@	conditions:
//@HDR@	
//@HDR@	The above copyright notice and this permission notice shall be
//@HDR@	included in all copies or substantial portions of the Software.
//@HDR@	
//@HDR@	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
//@HDR@	KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
//@HDR@	WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
//@HDR@	AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
//@HDR@	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
//@HDR@	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
//@HDR@	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
//@HDR@	OR OTHER DEALINGS IN THE SOFTWARE.
//
//hist#	2026-02-20 - Christopher.M.Caldwell0@gmail.com - Created
////////////////////////////////////////////////////////////////////////
//doc#	pictures.js - Javascript embedded in index.html with pictures
////////////////////////////////////////////////////////////////////////
var categorynames = new Array( %%CATEGORYNAMES%% );
var slides = new Array ( %%SLIDES%% );
var cookie_name = "pictures_%%CURRENT_GROUP%%";
var slidenum = 0;
var whereptr = 0;
var detailsptr = 0;
var detailsendptr = 0;
var upperleftptr = 0;
var upperrightptr = 0;
var currentpictureptr = 0;
var pictureurlptr = 0;
var prevbutid = 0;
var nextbutid = 0;
var randombutid = 0;
var timeoutvar = 0;
var repinc = 0;
var repmod = 0;

var WONTDISPLAY = new Array( "mov", "avi", "pdf", "html", "htm" );

var CLICKTODISPLAY = "click_to_display.jpg";

var myind = 0;

function read_cookie()
    {
    var cookievar = document.cookie.split("; ");
    for( i=0; i<cookievar.length; i++ )
        {
	if( cookievar[i].split("=")[0] == cookie_name )
	    {
	    var cval = cookievar[i].split("=")[1];
	    var cookietoks = cval.split(":");
	    slidenum = parseInt( cookietoks[0] );
	    }
	}
    }

function update_cookie()
    {
    expiredate = new Date;
    expiredate.setMonth(expiredate.getMonth()+6);
    var newcookie = slidenum;
    document.cookie = cookie_name + "=" + newcookie +
        ";expires="+expiredate.toGMTString();
    }


function match( current_slide )
    {
    with( window.document )
	{
	var i = categorynames.length;
	var search4exp = new RegExp( form.search4.value, "i" );
	if( slides[current_slide].u && slides[current_slide].u[myind] )
	    { return 0; }
	while( i-- > 0 )
	    {
	    var j = categorynames[i].v.length;
	    while( j-- > 0 )
	        {
		if( form[ "cb_"+i+"_"+j ].checked )
		    {
		    if( !slides[current_slide].f 	||
			!slides[current_slide].f[i]	||
			!slides[current_slide].f[i][j]	)
			    { return 0; }
		    }
		}
	    }
	if( form.search4.value != "" &&
	    !search4exp.test( slides[current_slide].c ) )
		{ return 0; }
	}
    return 1;
    }

var wid = 0;
var hgt = 0;

function picture_loaded()
    {
    if( repmod )
	{
	wid = window.innerWidth;
	hgt = window.innerHeight;
	}
    else
	{
	var o;

	var ultop = 0;
	var ulleft = 0;
	if(!upperleftptr) upperleftptr = document.getElementById("upperleft");
	for( o=upperleftptr; o!=null; o=o.offsetParent )
	    { ulleft += o.offsetLeft; ultop += o.offsetTop; }
	var lrtop = document.body.clientHeight - 60;

	var urleft = 0
	if(!upperrightptr) upperrightptr = document.getElementById("upperright");
	for( o=upperrightptr; o!=null; o=o.offsetParent )
	    { urleft += o.offsetLeft; }

	var detailstop = 0;
	if(!detailsptr) detailsptr = document.getElementById("details");
	for( o=detailsptr; o!=null; o=o.offsetParent )
	    { detailstop += o.offsetTop; }

	var detailsendtop = 0;
	if(!detailsendptr) detailsendptr = document.getElementById("detailsend");
	for( o=detailsendptr; o!=null; o=o.offsetParent )
	    { detailsendtop += o.offsetTop; }
	var detailsheight = detailsendtop - detailstop;
	wid = urleft - ulleft;
	hgt = lrtop - ultop - detailsheight;
	}

    var nwidth = currentpictureptr.naturalWidth;
    var nheight = currentpictureptr.naturalHeight;
    if( ! nwidth )	// Probably Internet Explorer.  SIGH.
	{
	var testimage = new Image();
	testimage.src = currentpictureptr.src;
	nwidth = testimage.width;
	nheight = testimage.height;
	}
    var wratio = wid / nwidth;
    var hratio = hgt / nheight;
    var ratio = ( (wratio < hratio) ? wratio : hratio );

    if(!currentpictureptr)
	currentpictureptr = document.getElementById("current_picture");
    currentpictureptr.style.width = Math.floor( nwidth * ratio );
    currentpictureptr.style.height = Math.floor( nheight * ratio );
    // alert("w="+nwidth+", h="+nheight+", ratio="+ratio+", cw="+Math.floor( nwidth * ratio )+", ch="+Math.floor( nheight * ratio ) );
    currentpictureptr.style.visibility = "visible";
    if( repmod ) { currentpictureptr.scrollIntoView(true); }
    }

var ptrs = {};
function put_up( n, inc, repmodearg )
    {
    slidenum = n;
    // alert("put_up="+slidenum);
    if(!currentpictureptr) currentpictureptr = document.getElementById("current_picture");
    // currentpictureptr.style.visibility = "hidden";
    var url = slides[slidenum].n;
    var ext = /\.([^\.]*)$/.exec( url );
    for( exti in WONTDISPLAY )
        {
	if( ext[1] == WONTDISPLAY[exti] ) { url = CLICKTODISPLAY; }
	}
    currentpictureptr.src = url;

    if(!pictureurlptr) pictureurlptr = document.getElementById("picture_url");
    pictureurlptr.href = slides[slidenum].n;

    if(!whereptr) whereptr = document.getElementById("where_picture");
    whereptr.innerHTML = "<a href=../../pictures.cgi?slide=" +
	slides[slidenum].n + "&current_group=%%CURRENT_GROUP%%&returnto=sorted>" + slides[slidenum].n + "</a>";

    var newtable = "<table cellspacing=0 cellpadding=0>";
    var i = categorynames.length;
    while( i-- > 0 )
        {
	var j = categorynames[i].v.length;
	while( j-- > 0 )
	    {
	    var attr = "#60a0e0";
	    if( slides[slidenum] &&
		slides[slidenum].f[i] &&
		slides[slidenum].f[i][j] )
	        {
		attr = "white";
		}
	    var ind = (i + "_" + j);
	    if( !ptrs[ind] )
	        { ptrs[ind] = document.getElementById("id_"+ind); }
	    ptrs[ind].style.backgroundColor = attr;
	    }
	}
    newtable += "<tr><td valign=top align=left>";
    newtable += slides[slidenum].c + "</td></tr></table>";
    if(!detailsptr) detailsptr = document.getElementById("details");
    detailsptr.innerHTML = newtable;

    if( timeoutvar ) { clearTimeout(timeoutvar); }
    if( repmodearg )
	{
	var p = ( inc<0 ? prevbutid : inc>0 ? nextbutid : randombutid );
	p.style.backgroundColor = "blue";

	if(inc<0)
	    { timeoutvar = setTimeout( function(){ next_slide(-1,1); }, 10000 ); }
	else if(inc>0)
	    { timeoutvar = setTimeout( function(){ next_slide( 1,1); }, 10000 ); }
	else
	    { timeoutvar = setTimeout( function(){ next_slide( 0,1); }, 10000 ); }
	repinc = inc;
	}
    }

function clear_buttons()
    {
    prevbutid  = (prevbutid   || document.getElementById("prevbut"  ));
    nextbutid  = (nextbutid   || document.getElementById("nextbut"  ));
    randombutid= (randombutid || document.getElementById("randombut"));
    prevbutid  .style.backgroundColor = "#d0d0d0";
    nextbutid  .style.backgroundColor = "#d0d0d0";
    randombutid.style.backgroundColor = "#d0d0d0";
    }

function next_slide( inc, repmodearg )
    {
    var next_slide_num = slidenum;
    var ctr = slides.length;
    var found = -1;
    repmod = repmodearg;

    clear_buttons();
    if( ! repmod )
        {
	if( timeoutvar ) { clearTimeout(timeoutvar); }
	// return;
	}

    if(!whereptr) whereptr = document.getElementById("where_picture");
    var prevwhere = whereptr.innerHTML;
    whereptr.innerHTML = "<blink>Searching...</blink>";

    while( (found<0) && (ctr-->0) )
        {
	next_slide_num =
	    ( inc
	    ? (slides.length + next_slide_num + inc) % slides.length
	    : Math.floor( Math.random() * slides.length )
	    );
	if( match(next_slide_num) )
	    { found = next_slide_num; }
	}
    if( found >= 0 )
        {
	put_up( found, inc, repmod );
	something = slides[slidenum].n;
	update_cookie();
	return 1;
	}
    whereptr.innerHTML = prevwhere;
    alert("No pictures match parameters");
    return 0;
    }

function get_slide()
    {
    clear_buttons();
    if( match(slidenum) )
        { put_up( slidenum, 0, 0 ); }
    else
        { next_slide( 1, 0 ); }
    }

read_cookie();
</script>
