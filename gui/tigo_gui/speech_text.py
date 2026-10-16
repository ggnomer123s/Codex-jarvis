"""Turn displayed Markdown into bounded plain speech, without reading code."""
import html
import re

MAX_SPEECH_CHARS = 6000


def spoken_text(text):
    lines, fence = [], ''
    for line in text.splitlines():
        opening = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if not fence and opening:
            fence = opening[1]
        elif fence and re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*', line):
            fence = ''
        elif not fence:
            lines.append(line)
    text = '\n'.join(lines)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'<https?://[^>]*>|https?://\S+', '', text)
    text = re.sub(r'</?[A-Za-z][^>]*>', '', text)
    text = re.sub(r'^\s{0,3}(?:#{1,6}\s+|>\s*|[-*+]\s+)', '', text, flags=re.M)
    text = re.sub(r'(`+|\*\*|__|~~)', '', text)
    text = html.unescape(text)
    if re.search(r'[\u0400-\u052f]', text):
        # Product pronunciation in Russian, without changing the displayed reply.
        text = re.sub(r'\bTigo\b', '\u0422\u0438\u0433\u043e', text, flags=re.I)
    text = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if len(text) > MAX_SPEECH_CHARS:
        ending = ' Продолжение — в чате.' if re.search(r'[\u0400-\u052f]', text) else ' The rest is in the chat.'
        text = text[:MAX_SPEECH_CHARS-len(ending)].rsplit(' ', 1)[0].rstrip() + ending
    return text
