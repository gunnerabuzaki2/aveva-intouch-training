#!/usr/bin/env python3
"""Simple paragraph merger: merge consecutive <p> into flowing paragraphs."""
import re
import os
import glob

LESSONS_DIR = "/mnt/d/Manuals/AVEVA/intouch-lessons/lessons"

def merge_paragraphs(html):
    """Merge consecutive <p>single-line</p> into flowing paragraphs."""
    
    # Pattern: find sequences of <p>text</p> that are short (single-line)
    # and merge them into one <p> with space-joined text
    def merge_p_sequence(match):
        items = re.findall(r'<p>(.*?)</p>', match.group(0), re.DOTALL)
        if not items:
            return match.group(0)
        
        # Filter out empty items and bullet markers
        texts = []
        for item in items:
            t = item.strip()
            if not t or t == '\uf0a7' or t == '' or t == '•':
                continue
            texts.append(t)
        
        if not texts:
            return match.group(0)
        
        # If only 1 item, return as-is
        if len(texts) == 1:
            return f'<p>{texts[0]}</p>'
        
        # Merge into flowing paragraph
        merged = ' '.join(texts)
        return f'<p>{merged}</p>'
    
    # Find sequences of <p>...</p> separated only by whitespace
    # Match 2+ consecutive <p> tags
    pattern = r'((?:\s*<p>.*?</p>\s*){2,})'
    html = re.sub(pattern, merge_p_sequence, html, flags=re.DOTALL)
    
    return html


def main():
    files = sorted(glob.glob(os.path.join(LESSONS_DIR, "L*.html")))
    for f in files:
        with open(f) as fh:
            html = fh.read()
        
        new_html = merge_paragraphs(html)
        
        if new_html != html:
            with open(f, 'w') as fh:
                fh.write(new_html)
            name = os.path.basename(f)
            old_p = html.count('<p>')
            new_p = new_html.count('<p>')
            print(f"  {name}: {old_p} → {new_p} paragraphs")

if __name__ == "__main__":
    main()
