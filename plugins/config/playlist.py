
# Default playlist format
m3uemptyheader = '#EXTM3U\n'
m3uheader = \
    '#EXTM3U url-tvg="http://1ttvapi.top/ttv.xmltv.xml.gz"\n'
# If you need the #EXTGRP field put this #EXTGRP:%(group)s\n after %(name)s\n.
m3uchanneltemplate = \
    '#EXTINF:-1 group-title="%(group)s" tvg-name="%(tvg)s" tvg-id="%(tvgid)s" tvg-logo="%(logo)s",%(name)s\n%(url)s\n'


xml_template = """<?xml version="1.0" encoding="utf-8"?>
<items>
<playlist_name>no_name</playlist_name>

%(items)s

</items>
"""

xml_channel_template = """
<channel>
<title><![CDATA[%(title)s]></title>
<description><![CDATA[<table><tr><td style="vertical-align: top"><img src="logos/open.png" height="128" width="128"></img></td><td>
<center>
<table style="width:100%%;font-size:16px;text-align:center;"><tr><td>%(description_title)s</td></tr></table>
<h2><font color="red">%(description)s</font></h2></td></tr></table></center>
<table style="width:100%%; padding-top:3px;padding-bottom:3px;"><tr height="4px" bgcolor="#cccccc"><td></td></tr></table>]]>
</description>
<playlist_url>%(hostport)s%(url)s</playlist_url>
</channel>
"""

xml_stream_template = """
<channel>
<title><![CDATA[%(title)s]></title>
<description><![CDATA[<table><tr><td style="vertical-align: top"><img src="logos/open.png" height="128" width="128"></img></td><td>
<center>
<table style="width:100%%;font-size:16px;text-align:center;"><tr><td>%(description_title)s</td></tr></table>
<h2><font color="red">%(description)s</font></h2></td></tr></table></center>
<table style="width:100%%; padding-top:3px;padding-bottom:3px;"><tr height="4px" bgcolor="#cccccc"><td></td></tr></table>]]>
</description>
<stream_url><![CDATA[ %(hostport)s%(url)s ]]></stream_url>
</channel>
"""
