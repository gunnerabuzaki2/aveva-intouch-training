#!/usr/bin/env python3
"""Post-process lessons to fix paragraph formatting.
Merges consecutive single-line <p> tags into flowing paragraphs.
Converts bullet lists to <ul><li> format.
"""
import re
import os
import glob

LESSONS_DIR = "/mnt/d/Manuals/AVEVA/intouch-lessons/lessons"

def fix_paragraphs(html):
    """Fix paragraph formatting in lesson HTML."""
    
    # Find the body content between h1 and quiz
    body_match = re.search(r'(<h1>.*?</h1>)(.*?)(<div class="quiz">)', html, re.DOTALL)
    if not body_match:
        return html
    
    h1 = body_match.group(1)
    body = body_match.group(2)
    quiz = body_match.group(3)
    
    # Extract all <p> content and screenshots
    elements = []
    for m in re.finditer(r'(<div class="screenshot">.*?</div>\s*</div>)|(<p>(.*?)</p>)', body, re.DOTALL):
        if m.group(1):  # Screenshot
            elements.append(('screenshot', m.group(1)))
        elif m.group(2):  # Paragraph
            text = m.group(3).strip()
            elements.append(('text', text))
    
    # Group consecutive text elements into paragraphs
    # Bullet points start with "" or similar markers
    paragraphs = []
    current_para = []
    in_bullet_list = False
    bullet_items = []
    
    for elem_type, content in elements:
        if elem_type == 'screenshot':
            # Flush current paragraph
            if current_para:
                paragraphs.append(('para', ' '.join(current_para)))
                current_para = []
            if bullet_items:
                paragraphs.append(('bullets', bullet_items))
                bullet_items = []
            paragraphs.append(('screenshot', content))
            continue
        
        # Check if this is a bullet point
        is_bullet = content.startswith('\uf0a7') or content.startswith('') or content.startswith('•')
        
        # Check if this is a section header-like text
        is_header = (
            len(content) < 60 and 
            not content.endswith('.') and 
            not content.startswith('The ') and
            not content.startswith('This ') and
            not content.startswith('In ') and
            not content.startswith('A ') and
            not content.startswith('An ') and
            not content.startswith('It ') and
            not content.startswith('When ') and
            not content.startswith('If ') and
            not content.startswith('Because ') and
            not content.startswith('Once ') and
            not content.startswith('Before ') and
            not content.startswith('After ') and
            not content.startswith('For ') and
            not content.startswith('System ') and
            not content.startswith('Application ') and
            not content.startswith('InTouch') and
            not content.startswith('AVEVA') and
            not content.startswith('ViewEngine') and
            not content.startswith('WindowMaker') and
            not content.startswith('WindowViewer') and
            not content.startswith('Graphics') and
            not content.startswith('Several') and
            not content.startswith('Each') and
            not content.startswith('One') and
            not content.startswith('Only') and
            not content.startswith('No') and
            not content.startswith('Do') and
            not content.startswith('However') and
            not content.startswith('Because') and
            len(content.split()) <= 6 and
            content[0].isupper()
        )
        
        # Empty or whitespace-only = paragraph break
        if not content.strip() or content.strip() == '\uf0a7':
            if current_para:
                paragraphs.append(('para', ' '.join(current_para)))
                current_para = []
            continue
        
        if is_bullet:
            if current_para:
                paragraphs.append(('para', ' '.join(current_para)))
                current_para = []
            bullet_items.append(content.lstrip('\uf0a7').strip())
            in_bullet_list = True
        elif is_header and not in_bullet_list:
            if current_para:
                paragraphs.append(('para', ' '.join(current_para)))
                current_para = []
            if bullet_items:
                paragraphs.append(('bullets', bullet_items))
                bullet_items = []
            # Treat as section header
            paragraphs.append(('header', content))
            in_bullet_list = False
        else:
            if bullet_items:
                paragraphs.append(('bullets', bullet_items))
                bullet_items = []
            in_bullet_list = False
            current_para.append(content)
    
    # Flush remaining
    if current_para:
        paragraphs.append(('para', ' '.join(current_para)))
    if bullet_items:
        paragraphs.append(('bullets', bullet_items))
    
    # Rebuild HTML
    new_body_parts = []
    for ptype, content in paragraphs:
        if ptype == 'screenshot':
            new_body_parts.append(content)
        elif ptype == 'para':
            if content.strip():
                new_body_parts.append(f'<p>{content}</p>')
        elif ptype == 'header':
            new_body_parts.append(f'<h2>{content}</h2>')
        elif ptype == 'bullets':
            if content:
                items = '\n'.join(f'  <li>{item}</li>' for item in content if item.strip())
                new_body_parts.append(f'<ul>\n{items}\n</ul>')
    
    new_body = '\n\n'.join(new_body_parts)
    
    # Reconstruct full HTML
    html = html[:body_match.start(2)] + new_body + html[body_match.end(2):]
    
    return html


def main():
    files = sorted(glob.glob(os.path.join(LESSONS_DIR, "L*.html")))
    fixed = 0
    for f in files:
        with open(f) as fh:
            html = fh.read()
        
        new_html = fix_paragraphs(html)
        
        if new_html != html:
            with open(f, 'w') as fh:
                fh.write(new_html)
            fixed += 1
            name = os.path.basename(f)
            # Count paragraphs before/after
            old_count = html.count('<p>')
            new_count = new_html.count('<p>')
            print(f"  {name}: {old_count} → {new_count} paragraphs")
    
    print(f"\nFixed {fixed}/{len(files)} lessons")


if __name__ == "__main__":
    main()
