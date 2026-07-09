#!/usr/bin/env python3
"""Apply caption fixes from JSON files to HTML lessons."""
import json
import os
import re
import glob

FIXES_DIR = "/mnt/d/Manuals/AVEVA/intouch-lessons/fixes"
LESSONS_DIR = "/mnt/d/Manuals/AVEVA/intouch-lessons/lessons"


def apply_fixes():
    fix_files = glob.glob(os.path.join(FIXES_DIR, "*_captions.json"))
    total_fixed = 0
    
    for fix_file in fix_files:
        lesson_id = os.path.basename(fix_file).replace("_captions.json", "")
        
        with open(fix_file) as f:
            captions = json.load(f)
        
        # Find the lesson HTML file
        html_files = glob.glob(os.path.join(LESSONS_DIR, f"{lesson_id}-*.html"))
        if not html_files:
            print(f"  WARNING: No HTML found for {lesson_id}")
            continue
        
        html_file = html_files[0]
        with open(html_file) as f:
            html = f.read()
        
        fixed = 0
        for filename, caption in captions.items():
            # Escape caption for HTML
            caption_escaped = caption.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            
            # Fix alt text using string replacement (not regex)
            old_alt = f'src="../images/{filename}" alt="'
            # Find and replace the alt text after this image
            idx = html.find(old_alt)
            if idx >= 0:
                # Find the closing quote of the alt attribute
                start = idx + len(old_alt)
                end = html.find('"', start)
                if end > start:
                    old_alt_full = html[idx:end+1]
                    new_alt_full = f'src="../images/{filename}" alt="{caption_escaped}"'
                    html = html.replace(old_alt_full, new_alt_full, 1)
                    fixed += 1
            
            # Fix caption div using string replacement
            caption_old = f'<img src="../images/{filename}"'
            cap_idx = html.find(caption_old)
            if cap_idx >= 0:
                # Find the next caption div after this image
                cap_div_start = html.find('<div class="caption">', cap_idx)
                cap_div_end = html.find('</div>', cap_div_start)
                if cap_div_start > cap_idx and cap_div_end > cap_div_start:
                    old_cap = html[cap_div_start:cap_div_end+6]
                    new_cap = f'<div class="caption">{caption_escaped}</div>'
                    html = html.replace(old_cap, new_cap, 1)
                    fixed += 1
        
        with open(html_file, 'w') as f:
            f.write(html)
        
        print(f"  {lesson_id}: {fixed} replacements for {len(captions)} captions")
        total_fixed += fixed
    
    print(f"\nTotal: {total_fixed} replacements across {len(fix_files)} lessons")


if __name__ == "__main__":
    apply_fixes()
