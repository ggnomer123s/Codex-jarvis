"""Fenced code blocks and inert Markdown; no remote images or raw HTML."""
import html
import re
from urllib.parse import urlsplit
from PySide6.QtGui import QTextDocument


def markdown_html(text):
    doc = QTextDocument()
    doc.setMarkdown(text, QTextDocument.MarkdownFeature.MarkdownDialectGitHub | QTextDocument.MarkdownFeature.MarkdownNoHTML)
    rendered = doc.toHtml()
    # Qt generates canonical HTML. Remove image elements before a QML document
    # sees them; neither local-file nor remote image fetching is permitted here.
    rendered = re.sub(r'<img\b[^>]*>', '[image]', rendered, flags=re.I)
    rendered = rendered.replace('color:#0000ff', 'color:#73e3d2')
    rendered = re.sub(r'font-size:\s*[\d.]+pt;?', '', rendered)
    rendered = re.sub(r'font-family:[^;\"]*;?', '', rendered)
    def link(match):
        url = html.unescape(match[1])
        try:
            allowed = urlsplit(url).scheme.lower() in ('https','http')
        except ValueError:
            allowed = False
        return match[0] if allowed else '<a>'
    rendered = re.sub(r'<a href="([^"]*)"[^>]*>', link, rendered)
    return rendered


def message_blocks(text, markdown=True):
    if not markdown:
        return [{'kind':'plain','text':text,'language':''}]
    blocks, prose, code = [], [], None
    fence, language = '', ''
    def flush_prose():
        if prose:
            source = ''.join(prose)
            blocks.append({'kind':'markdown','text':markdown_html(source),'language':''})
            prose.clear()
    for line in text.splitlines(keepends=True):
        opening = re.match(r'^ {0,3}(`{3,}|~{3,})([^\r\n]*)',line)
        if code is None and opening:
            flush_prose()
            fence, language, code = opening[1], opening[2].strip()[:60], []
        elif code is not None and re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}[ \t]*[\r\n]*',line):
            blocks.append({'kind':'code','text':''.join(code),'language':language})
            code = None
        elif code is None:
            prose.append(line)
        else:
            code.append(line)
    if code is not None:
        blocks.append({'kind':'code','text':''.join(code),'language':language})
    flush_prose()
    return blocks or [{'kind':'plain','text':'','language':''}]
