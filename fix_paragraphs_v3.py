#!/usr/bin/env python3
"""Careful paragraph merger: merge <p> across section boundaries."""
import re
import os
import glob

LESSONS_DIR = "/mnt/d/Manuals/AVEVA/intouch-lessons/lessons"

def merge_paragraphs(html):
    """Merge consecutive <p>single-line</p> into flowing paragraphs.
    
    Rules:
    - Merge 2+ consecutive <p> tags that contain text (not just bullets)
    - Stop merging at <h2>, <div class="screenshot">, <ul>, <table>
    - Keep bullet items as separate <p> (they're list items)
    - Don't merge paragraphs that are too long (>500 chars) — they're already flowing
    """
    
    lines = html.split('\n')
    result = []
    p_buffer = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check if this is a mergeable <p> tag
        p_match = re.match(r'^<p>(.*?)</p>$', stripped)
        
        if p_match:
            content = p_match.group(1).strip()
            
            # Skip empty paragraphs
            if not content:
                if p_buffer:
                    result.append(merge_buffer(p_buffer))
                    p_buffer = []
                continue
            
            # Skip bullet markers
            if content in ('\uf0a7', '', '•', '–'):
                if p_buffer:
                    result.append(merge_buffer(p_buffer))
                    p_buffer = []
                continue
            
            # Skip if this paragraph is already long (>500 chars)
            if len(content) > 500:
                if p_buffer:
                    result.append(merge_buffer(p_buffer))
                    p_buffer = []
                result.append(stripped)
                continue
            
            # Add to buffer
            p_buffer.append(content)
        else:
            # Non-paragraph line — flush buffer
            if p_buffer:
                result.append(merge_buffer(p_buffer))
                p_buffer = []
            result.append(line)
    
    # Flush remaining
    if p_buffer:
        result.append(merge_buffer(p_buffer))
    
    return '\n'.join(result)


def merge_buffer(buffer):
    """Merge a buffer of paragraph texts into one <p> tag."""
    if not buffer:
        return ''
    if len(buffer) == 1:
        return f'<p>{buffer[0]}</p>'
    
    # Join with space, creating flowing paragraph
    merged = ' '.join(buffer)
    return f'<p>{merged}</p>'


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
