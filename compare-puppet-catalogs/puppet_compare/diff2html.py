#! /usr/bin/python
# coding=utf-8
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Transform a unified diff from stdin to a colored
# side-by-side HTML page on stdout.
#
# Authors: Olivier Matz <zer0@droids-corp.org>
#          Alan De Smet <adesmet@cs.wisc.edu>
#          Sergey Satskiy <sergey.satskiy@gmail.com>
#          scito <info at scito.ch>
#          Giuseppe Lavagetto <glavagetto@wikimedia.org>
#
# Inspired by diff2html.rb from Dave Burt <dave (at) burt.id.au>
# (mainly for html theme)
#
# TODO:
# - The sane function currently mashes non-ASCII characters to "."
#   Instead be clever and convert to something like "xF0"
#   (the hex value), and mark with a <span>.  Even more clever:
#   Detect if the character is "printable" for whatever definition,
#   and display those directly.

# Modifications by Giuseppe Lavagetto (c) 2014 The Wikimedia Foundation

import sys
import re
import htmlentitydefs
import getopt
import StringIO
import codecs
import datetime
from functools import reduce
try:
    from simplediff import diff, string_diff
except ImportError:
    sys.stderr.write(
        "info: simplediff module not found, only linediff is available\n")
    sys.stderr.write(
        "info: it can be downloaded at https://github.com/paulgb/simplediff\n")

# minimum line size, we add a zero-sized breakable space every
# LINESIZE characters
linesize = 20
tabsize = 8
show_CR = False
encoding = "utf-8"
lang = "en"
algorithm = 0

desc = "File comparison"
dtnow = datetime.datetime.now()
modified_date = "%s+01:00" % dtnow.isoformat()

html_hdr = """<!DOCTYPE html>
<html lang="{5}" dir="ltr"
    xmlns:dc="http://purl.org/dc/terms/">
<head>
    <meta charset="{1}" />
    <meta name="generator" content="diff2html.py (http://git.droids-corp.org/gitweb/?p=diff2html)" />
    <!--meta name="author" content="Fill in" /-->
    <title>HTML Diff{0}</title>
    <link rel="shortcut icon" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAgMAAABinRfyAAAACVBMVEXAAAAAgAD///+K/HwIAAAAJUlEQVQI12NYBQQM2IgGBQ4mCIEQW7oyK4phampkGIQAc1G1AQCRxCNbyW92oQAAAABJRU5ErkJggg==" type="image/png" />
    <meta property="dc:language" content="{5}" />
    <!--meta property="dc:date" content="{3}" /-->
    <meta property="dc:modified" content="{4}" />
    <meta name="description" content="Differences in catalogs for {2}" />
    <meta property="dc:abstract" content="{2}" />
    <style>
        table {{ border:0px; border-collapse:collapse; width: 100%; font-size:0.75em; font-family: Lucida Console, monospace }}
        td.line {{ color:#8080a0 }}
        th {{ background: black; color: white }}
        tr.diffunmodified td {{ background: #D0D0E0 }}
        tr.diffhunk td {{ background: #A0A0A0 }}
        tr.diffadded td {{ background: #CCFFCC }}
        tr.diffdeleted td {{ background: #FFCCCC }}
        tr.diffchanged td {{ background: #FFFFA0 }}
        span.diffchanged2 {{ background: #E0C880 }}
        span.diffponct {{ color: #B08080 }}
        tr.diffmisc td {{}}
        tr.diffseparator td {{}}
    </style>
</head>
<body>
<h1>Catalog compilation for <span style="color: #EA3030">{2}</span></h1>

<div class="hero-unit">
<h2>Puppet 3</h2>
<ul>
    <li><a href="../compiled/puppet_catalogs_3/{2}.pson">Compiled catalog</a></li>
    <li><a href="../compiled/puppet_catalogs_3/{2}.warnings">Compilation errors and warnings</a></li>
</ul>
</div>
<div class="hero-unit">
<h2>Puppet 2.7</h2>
<ul>
    <li><a href="../compiled/puppet_catalogs_2.7/{2}.pson">Compiled catalog</a></li>
    <li><a href="../compiled/puppet_catalogs_2.7/{2}.warnings">Compilation errors and warnings</a></li>
</ul>
</div>
<h2>Diffs</h2>

"""

html_footer = """
<footer>
    <p>Modified at {1}. HTML formatting created by <a href="http://git.droids-corp.org/gitweb/?p=diff2html;a=summary">diff2html</a>.    </p>
</footer>
</body></html>
"""

table_hdr = """
        <table class="diff">
"""

table_footer = """
</table>
"""

DIFFON = "\x01"
DIFFOFF = "\x02"

buf = []
add_cpt, del_cpt = 0, 0
line1, line2 = 0, 0
hunk_off1, hunk_size1, hunk_off2, hunk_size2 = 0, 0, 0, 0


# Characters we're willing to word wrap on
WORDBREAK = " \t;.,/):-"


def sane(x):
    r = ""
    for i in x:
        j = ord(i)
        if i not in ['\t', '\n'] and (j < 32):
            r = r + "."
        else:
            r = r + i
    return r


def linediff(s, t):
    '''
    Original line diff algorithm of diff2html. It's character based.
    '''
    if len(s):
        s = unicode(reduce(lambda x, y: x + y, [sane(c) for c in s]))
    if len(t):
        t = unicode(reduce(lambda x, y: x + y, [sane(c) for c in t]))

    m, n = len(s), len(t)
    d = [[(0, 0) for i in range(n + 1)] for i in range(m + 1)]

    d[0][0] = (0, (0, 0))
    for i in range(m + 1)[1:]:
        d[i][0] = (i, (i - 1, 0))
    for j in range(n + 1)[1:]:
        d[0][j] = (j, (0, j - 1))

    for i in range(m + 1)[1:]:
        for j in range(n + 1)[1:]:
            if s[i - 1] == t[j - 1]:
                cost = 0
            else:
                cost = 1
            d[i][j] = min((d[i - 1][j][0] + 1, (i - 1, j)),
                          (d[i][j - 1][0] + 1, (i, j - 1)),
                          (d[i - 1][j - 1][0] + cost, (i - 1, j - 1)))

    l = []
    coord = (m, n)
    while coord != (0, 0):
        l.insert(0, coord)
        x, y = coord
        coord = d[x][y][1]

    l1 = []
    l2 = []

    for coord in l:
        cx, cy = coord
        child_val = d[cx][cy][0]

        father_coord = d[cx][cy][1]
        fx, fy = father_coord
        father_val = d[fx][fy][0]

        diff = (cx - fx, cy - fy)

        if diff == (0, 1):
            l1.append("")
            l2.append(DIFFON + t[fy] + DIFFOFF)
        elif diff == (1, 0):
            l1.append(DIFFON + s[fx] + DIFFOFF)
            l2.append("")
        elif child_val - father_val == 1:
            l1.append(DIFFON + s[fx] + DIFFOFF)
            l2.append(DIFFON + t[fy] + DIFFOFF)
        else:
            l1.append(s[fx])
            l2.append(t[fy])

    r1, r2 = (reduce(lambda x, y: x + y, l1), reduce(lambda x, y: x + y, l2))
    return r1, r2


def diff_changed(old, new):
    '''
    Returns the differences basend on characters between two strings
    wrapped with DIFFON and DIFFOFF using `diff`.
    '''
    con = {'=': (lambda x: x),
           '+': (lambda x: DIFFON + x + DIFFOFF),
           '-': (lambda x: '')}
    return "".join([(con[a])("".join(b)) for a, b in diff(old, new)])


def diff_changed_ts(old, new):
    '''
    Returns a tuple for a two sided comparison based on characters, see `diff_changed`.
    '''
    return (diff_changed(new, old), diff_changed(old, new))


def word_diff(old, new):
    '''
    Returns the difference between the old and new strings based on words. Punctuation is not part of the word.

    Params:
        old the old string
        new the new string

    Returns:
        the output of `diff` on the two strings after splitting them
        on whitespace (a list of change instructions; see the docstring
        of `diff`)
    '''
    separator_pattern = '(\W+)'
    return diff(re.split(separator_pattern, old, flags=re.UNICODE),
                re.split(separator_pattern, new, flags=re.UNICODE))


def diff_changed_words(old, new):
    '''
    Returns the difference between two strings based on words (see `word_diff`)
    wrapped with DIFFON and DIFFOFF.

    Returns:
        the output of the diff expressed delimited with DIFFON and DIFFOFF.
    '''
    con = {'=': (lambda x: x),
           '+': (lambda x: DIFFON + x + DIFFOFF),
           '-': (lambda x: '')}
    return "".join([(con[a])("".join(b)) for a, b in word_diff(old, new)])


def diff_changed_words_ts(old, new):
    '''
    Returns a tuple for a two sided comparison based on words, see `diff_changed_words`.
    '''
    return (diff_changed_words(new, old), diff_changed_words(old, new))


def convert(s, linesize=0, ponct=0):
    i = 0
    t = u""
    for c in s:
        # used by diffs
        if c == DIFFON:
            t += u'<span class="diffchanged2">'
        elif c == DIFFOFF:
            t += u"</span>"

        # special html chars
        elif ord(c) in htmlentitydefs.codepoint2name:
            t += u"&%s;" % (htmlentitydefs.codepoint2name[ord(c)])
            i += 1

        # special highlighted chars
        elif c == "\t" and ponct == 1:
            n = tabsize - (i % tabsize)
            if n == 0:
                n = tabsize
            t += (u'<span class="diffponct">&raquo;</span>' +
                  '&nbsp;' * (n - 1))
        elif c == " " and ponct == 1:
            t += u'<span class="diffponct">&middot;</span>'
        elif c == "\n" and ponct == 1:
            if show_CR:
                t += u'<span class="diffponct">\</span>'
        else:
            t += c
            i += 1

        if linesize and (WORDBREAK.count(c) == 1):
            t += u'&#8203;'
            i = 0
        if linesize and i > linesize:
            i = 0
            t += u"&#8203;"

    return t


def add_comment(s, output_file):
    output_file.write(
        ('<tr class="diffmisc"><td colspan="4">%s</td></tr>\n' % convert(s)).encode(encoding))


def add_filename(f1, f2, output_file):
    output_file.write(("<tr><th colspan='2'>%s</th>" %
                      convert(f1, linesize=linesize)).encode(encoding))
    output_file.write(("<th colspan='2'>%s</th></tr>\n" %
                      convert(f2, linesize=linesize)).encode(encoding))


def add_hunk(output_file, show_hunk_infos):
    if show_hunk_infos:
        output_file.write(
            '<tr class="diffhunk"><td colspan="2">Offset %d, %d lines modified</td>' % (hunk_off1, hunk_size1))
        output_file.write(
            '<td colspan="2">Offset %d, %d lines modified</td></tr>\n' % (hunk_off2, hunk_size2))
    else:
        # &#8942; - vertical ellipsis
        output_file.write(
            '<tr class="diffhunk"><td colspan="2">&#8942;</td><td colspan="2">&#8942;</td></tr>')


def add_line(s1, s2, output_file):
    global line1
    global line2

    orig1 = s1
    orig2 = s2

    if s1 is None and s2 is None:
        type_name = "unmodified"
    elif s1 is None or s1 == "":
        type_name = "added"
    elif s2 is None or s1 == "":
        type_name = "deleted"
    elif s1 == s2:
        type_name = "unmodified"
    else:
        type_name = "changed"
        if algorithm == 1:
            s1, s2 = diff_changed_words_ts(orig1, orig2)
        elif algorithm == 2:
            s1, s2 = diff_changed_ts(orig1, orig2)
        else:  # default
            s1, s2 = linediff(orig1, orig2)

    output_file.write(('<tr class="diff%s">' % type_name).encode(encoding))
    if s1 is not None and s1 != "":
        output_file.write(
            ('<td class="diffline">%d </td>' % line1).encode(encoding))
        output_file.write('<td class="diffpresent">'.encode(encoding))
        output_file.write(
            convert(s1, linesize=linesize, ponct=1).encode(encoding))
        output_file.write('</td>')
    else:
        s1 = ""
        output_file.write('<td colspan="2"> </td>')

    if s2 is not None and s2 != "":
        output_file.write(
            ('<td class="diffline">%d </td>' % line2).encode(encoding))
        output_file.write('<td class="diffpresent">')
        output_file.write(
            convert(s2, linesize=linesize, ponct=1).encode(encoding))
        output_file.write('</td>')
    else:
        s2 = ""
        output_file.write('<td colspan="2"></td>')

    output_file.write('</tr>\n')

    if s1 != "":
        line1 += 1
    if s2 != "":
        line2 += 1


def empty_buffer(output_file):
    global buf
    global add_cpt
    global del_cpt

    if del_cpt == 0 or add_cpt == 0:
        for l in buf:
            add_line(l[0], l[1], output_file)

    elif del_cpt != 0 and add_cpt != 0:
        l0, l1 = [], []
        for l in buf:
            if l[0] is not None:
                l0.append(l[0])
            if l[1] is not None:
                l1.append(l[1])
        max_len = (len(l0) > len(l1)) and len(l0) or len(l1)
        for i in range(max_len):
            s0, s1 = "", ""
            if i < len(l0):
                s0 = l0[i]
            if i < len(l1):
                s1 = l1[i]
            add_line(s0, s1, output_file)

    add_cpt, del_cpt = 0, 0
    buf = []


def parse_input(input_file, output_file, input_file_name, output_file_name,
                exclude_headers, show_hunk_infos, desc):
    global add_cpt, del_cpt
    global line1, line2
    global hunk_off1, hunk_size1, hunk_off2, hunk_size2

    if not exclude_headers:
        title_suffix = ' ' + input_file_name
        output_file.write(html_hdr.format(
            title_suffix, encoding, desc, "", modified_date, lang).encode(encoding))
    output_file.write(table_hdr.encode(encoding))

    while True:
        l = input_file.readline()
        if l == "":
            break

        m = re.match('^--- ([^\s]*)', l)
        if m:
            empty_buffer(output_file)
            file1 = m.groups()[0]
            while True:
                l = input_file.readline()
                m = re.match('^\+\+\+ ([^\s]*)', l)
                if m:
                    file2 = m.groups()[0]
                    break
            add_filename(file1, file2, output_file)
            hunk_off1, hunk_size1, hunk_off2, hunk_size2 = 0, 0, 0, 0
            continue

        m = re.match("@@ -(\d+),?(\d*) \+(\d+),?(\d*)", l)
        if m:
            empty_buffer(output_file)
            hunk_data = map(lambda x: x == "" and 1 or int(x), m.groups())
            hunk_off1, hunk_size1, hunk_off2, hunk_size2 = hunk_data
            line1, line2 = hunk_off1, hunk_off2
            add_hunk(output_file, show_hunk_infos)
            continue

        if hunk_size1 == 0 and hunk_size2 == 0:
            empty_buffer(output_file)
            add_comment(l, output_file)
            continue

        if re.match("^\+", l):
            add_cpt += 1
            hunk_size2 -= 1
            buf.append((None, l[1:]))
            continue

        if re.match("^\-", l):
            del_cpt += 1
            hunk_size1 -= 1
            buf.append((l[1:], None))
            continue

        if re.match("^\ ", l) and hunk_size1 and hunk_size2:
            empty_buffer(output_file)
            hunk_size1 -= 1
            hunk_size2 -= 1
            buf.append((l[1:], l[1:]))
            continue

        empty_buffer(output_file)
        add_comment(l, output_file)

    empty_buffer(output_file)
    output_file.write(table_footer.encode(encoding))
    if not exclude_headers:
        output_file.write(
            html_footer.format("", dtnow.strftime("%d.%m.%Y")).encode(encoding))


def stream_parse(txt=None, output_file_name='', enc=None,
                 show_cr=False, show_hunk_infos=True, verbose=False, fqdn=None):
    global linesize, tabsize
    global show_CR
    global encoding
    global algorithm

    exclude_headers = False

    if enc is not None:
        encoding = enc

    if show_cr is not None:
        show_CR = show_cr

    input_file = StringIO.StringIO(txt)

    if output_file_name:
        output_file = codecs.open(output_file_name, "w")
    else:
        output_file = codecs.getwriter(encoding)(sys.stdout)

    if fqdn:
        desc = fqdn
    else:
        desc = 'Catalog differences'

    parse_input(input_file, output_file, '', output_file_name,
                exclude_headers, show_hunk_infos, desc)
