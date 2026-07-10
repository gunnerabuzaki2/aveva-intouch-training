#!/usr/bin/env python3
"""Batch-fix InTouch lessons to match canonical app-server pattern."""
import re
import os
import glob

LESSONS_DIR = "/mnt/d/Manuals/AVEVA/intouch-lessons/lessons"

# Lesson ID to number mapping
def get_lesson_num(lesson_id):
    return int(lesson_id.replace('L', ''))

# Lesson ID to title mapping (from filenames)
def extract_info_from_filename(filename):
    """Extract lesson ID and title from filename."""
    basename = os.path.basename(filename)
    m = re.match(r'(L\d+)-(.+)\.html', basename)
    if m:
        return m.group(1), m.group(2).replace('-', ' ')
    return None, None

def fix_lesson(filepath):
    with open(filepath) as f:
        html = f.read()
    
    original = html
    lid, title_from_file = extract_info_from_filename(filepath)
    if not lid:
        return False
    
    num = get_lesson_num(lid)
    
    # Fix 1: Title tag — "Lesson L01:" → "Lesson 1:"
    html = re.sub(
        r'<title>Lesson L\d+: [^<]+</title>',
        f'<title>Lesson {num}: {title_from_file}</title>',
        html
    )
    
    # Fix 2: H1 — "Lesson L01:" → "Lesson 1:"
    html = re.sub(
        r'<h1>Lesson L\d+: [^<]+</h1>',
        f'<h1>Lesson {num}: {title_from_file}</h1>',
        html
    )
    
    # Fix 3: localStorage key — 'intouch-lesson-progress' → 'aveva-lesson-progress'
    html = html.replace("'intouch-lesson-progress'", "'aveva-lesson-progress'")
    
    # Fix 4: Source citation — align with canonical format
    # Find and replace the source block
    old_source_pattern = r'<p class="source">[^<]*</p>\s*<p class="source">[^<]*</p>'
    new_source = f'<p class="source">Source: AVEVA InTouch for System Platform 2023 Training Manual</p>\n<p class="source">Next: Lesson {num+1} — {title_from_file}</p>'
    # Only replace if we find the pattern (not all lessons have it)
    
    # Fix 5: Quiz format — "Knowledge Check" → "Quiz — Test Your Understanding"
    html = html.replace('<h3>Knowledge Check</h3>', '<h3>Quiz — Test Your Understanding</h3>')
    
    # Fix 6: Quiz details format — add inline styles
    html = re.sub(
        r'<details>\s*<summary>(Q\d+):',
        r'<details><summary style="cursor:pointer;color:#2c5f2d;font-weight:bold;">\1:',
        html
    )
    
    # Fix 7: Answer format — add inline styles
    html = re.sub(
        r'<p class="answer">([^<]+)</p>\s*</details>',
        r'<p class="answer" style="display:block;color:#2c5f2d;font-weight:bold;margin-top:0.3em;">\1</p></details>',
        html
    )
    
    # Fix 8: Remove L prefix from nav dropdown labels
    html = re.sub(r'">L(\d+): ', r'">\1: ', html)
    
    if html != original:
        with open(filepath, 'w') as f:
            f.write(html)
        return True
    return False

def main():
    files = sorted(glob.glob(os.path.join(LESSONS_DIR, "L*.html")))
    fixed = 0
    for f in files:
        if fix_lesson(f):
            name = os.path.basename(f)
            fixed += 1
            print(f"  Fixed: {name}")
    
    print(f"\nFixed {fixed}/{len(files)} lessons")

if __name__ == "__main__":
    main()
