#!/usr/bin/env python3
"""Clean PDF extraction artifacts from lesson text and regenerate all lessons."""
import re
import os
import json
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
LESSONS_DIR = os.path.join(BASE_DIR, "lessons")
PLAN_FILE = os.path.join(BASE_DIR, "lesson_plan.json")
COMPLETE_MD = "/home/eng_zaki/.hermes/skills/software-development/aveva-intouch/references/aveva_intouch_complete.md"


def clean_text(text):
    """Remove PDF extraction artifacts from text."""
    lines = text.split('\n')
    cleaned = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines (preserve as paragraph breaks)
        if not stripped:
            cleaned.append('')
            continue
        
        # Skip "Do Not Copy" watermark lines
        if stripped == 'Do Not Copy':
            continue
        
        # Skip section/module header lines (PDF internal headers)
        if re.match(r'^Section\s+\d+\s*[–-]', stripped):
            continue
        if re.match(r'^Module\s+\d+\s*[–-]', stripped):
            continue
        if re.match(r'^Lab\s+\d+\s*[–-]', stripped):
            continue
        
        # Skip lines that are JUST page number headers
        # Pattern: "1-7 AVEVA™ InTouch for System Platform 2023"
        # Pattern: "AVEVA™ Training"
        # Pattern: "AVEVA™ InTouch for System Platform 2023"
        if re.match(r'^\d+-\d+\s+AVEVA', stripped):
            continue
        if stripped in ('AVEVA™ Training', 'AVEVA™ InTouch for System Platform 2023',
                        'AVEVA InTouch for System Platform 2023',
                        'AVEVA™ Training Manual', 'Training Manual'):
            continue
        
        # Skip standalone page numbers like "1-7" or "2-15"
        if re.match(r'^\d+-\d+$', stripped):
            continue
        
        # Skip lines that are just "Do Not Copy" followed by page info
        if stripped.startswith('Do Not Copy') and len(stripped) < 50:
            continue
        
        # Clean "Do Not Copy" prefix from lines that have content after it
        if stripped.startswith('Do Not Copy'):
            stripped = stripped[len('Do Not Copy'):].strip()
            if not stripped:
                continue
        
        # Skip very short artifact lines
        if stripped in ('AVEVA™', 'AVEVA', 'Revision A', 'August 2023'):
            continue
        
        # Clean leading/trailing whitespace
        line = stripped
        cleaned.append(line)
    
    # Remove consecutive empty lines (max 1)
    result = []
    prev_empty = False
    for line in cleaned:
        if line == '':
            if not prev_empty:
                result.append(line)
            prev_empty = True
        else:
            result.append(line)
            prev_empty = False
    
    return '\n'.join(result)


def detect_section_headers(text, lesson_id, module_title):
    """Detect natural section breaks and add h2 headers."""
    # Common section patterns in AVEVA training (with optional AVEVA prefix)
    section_patterns = [
        (r'(?:AVEVA[™\s]*(?:System\s+Platform\s+)?)?Create\s+the\s+Galaxy', 'Creating the Galaxy'),
        (r'(?:AVEVA[™\s]*)?Import\s+the\s+Training\s+Objects', 'Import the Training Objects'),
        (r'(?:AVEVA[™\s]*)?Configure\s+the\s+Platforms?', 'Configure the Platforms'),
        (r'(?:AVEVA[™\s]*)?Deploy\s+the\s+Galaxy', 'Deploy the Galaxy'),
        (r'(?:AVEVA[™\s]*)?Verify\s+with\s+Object\s+Viewer', 'Verify with Object Viewer'),
        (r'^Introduction\s+In\s+this\s+lab', 'Lab Introduction'),
        (r'^Objectives\s+Upon\s+completion', 'Lab Objectives'),
        (r'^In\s+this\s+lab', 'Lab Introduction'),
        (r'^Upon\s+completion\s+of\s+this', 'Lab Objectives'),
        (r'(?:AVEVA[™\s]*)?System\s+Platform\s+Overview', 'System Platform Overview'),
        (r'(?:AVEVA[™\s]*)?System\s+Platform\s+Components', 'System Platform Components'),
        (r'(?:AVEVA[™\s]*)?ArchestrA\s+Technology', 'ArchestrA Technology'),
        (r'(?:AVEVA[™\s]*)?WindowMaker\s+Interface', 'WindowMaker Interface'),
        (r'(?:AVEVA[™\s]*)?WindowViewer\s+Runtime', 'WindowViewer Runtime'),
        (r'(?:AVEVA[™\s]*)?Security\s+Overview', 'Security Overview'),
        (r'(?:AVEVA[™\s]*)?Alarm\s+Overview', 'Alarm Overview'),
        (r'(?:AVEVA[™\s]*)?Trend\s+Overview', 'Trend Overview'),
        (r'(?:AVEVA[™\s]*)?Symbol\s+Overview', 'Symbol Overview'),
        (r'(?:AVEVA[™\s]*)?Graphic\s+Editor\s+Overview', 'Graphic Editor Overview'),
        (r'(?:AVEVA[™\s]*)?Custom\s+Properties', 'Custom Properties'),
        (r'(?:AVEVA[™\s]*)?OwningObject\s+Property', 'OwningObject Property'),
        (r'(?:AVEVA[™\s]*)?Scripts?\s+in\s+Graphics', 'Scripts in Graphics'),
        (r'(?:AVEVA[™\s]*)?Galaxy\s+Styles', 'Galaxy Styles'),
        (r'(?:AVEVA[™\s]*)?Widgets?\s+Overview', 'Widgets Overview'),
        (r'(?:AVEVA[™\s]*)?Web\s+Client\s+Overview', 'Web Client Overview'),
        (r'(?:AVEVA[™\s]*)?Signed\s+Writes?', 'Signed Writes'),
        (r'(?:AVEVA[™\s]*)?Runtime\s+Customization', 'Runtime Customization'),
        (r'(?:AVEVA[™\s]*)?Historization\s+Overview', 'Historization Overview'),
        (r'(?:AVEVA[™\s]*)?Real-Time\s+Trending', 'Real-Time Trending'),
        (r'(?:AVEVA[™\s]*)?Multi\s+Pens?\s+Trend', 'Multi-Pen Trend'),
        (r'(?:AVEVA[™\s]*)?Historian\s+Client', 'Historian Client'),
        (r'(?:AVEVA[™\s]*)?Encryption', 'Encrypted Communication'),
        (r'(?:AVEVA[™\s]*)?System\s+Requirements', 'System Requirements'),
        (r'(?:AVEVA[™\s]*)?Licensing', 'Licensing'),
        (r'(?:AVEVA[™\s]*)?General\s+and\s+Operational\s+Permissions', 'Security Permissions'),
        (r'(?:AVEVA[™\s]*)?Authentication\s+Mode', 'Authentication Mode'),
        (r'(?:AVEVA[™\s]*)?Roles?\s+and\s+Users?', 'Roles and Users'),
        (r'(?:AVEVA[™\s]*)?Alarm\s+Severity', 'Alarm Severity'),
        (r'(?:AVEVA[™\s]*)?Alarm\s+Aggregation', 'Alarm Aggregation'),
        (r'(?:AVEVA[™\s]*)?Alarm\s+Client', 'Alarm Client'),
        (r'(?:AVEVA[™\s]*)?Historical\s+Alarms?', 'Historical Alarms'),
        (r'(?:AVEVA[™\s]*)?Trend\s+Pens?', 'Trend Pens'),
        (r'(?:AVEVA[™\s]*)?Multi\s+Pens?\s+Trend', 'Multi-Pen Trend'),
        (r'(?:AVEVA[™\s]*)?Inactivity', 'Inactivity and Timeout'),
        (r'(?:AVEVA[™\s]*)?MenuBar', 'Menu Bar Security'),
        (r'(?:AVEVA[™\s]*)?EnableDisableKeys', 'Key Lockdown'),
        (r'(?:AVEVA[™\s]*)?Web\s+Client\s+Configuration', 'Web Client Configuration'),
    ]
    
    paragraphs = text.split('\n\n')
    result = []
    
    for i, para in enumerate(paragraphs):
        stripped = para.strip()
        if not stripped:
            continue
        
        # Check if this paragraph starts a new section
        first_line = stripped.split('\n')[0].strip()
        added_header = False
        
        for pattern, header in section_patterns:
            if re.match(pattern, first_line, re.IGNORECASE):
                # Don't add duplicate headers
                if not any(f'<h2>{header}</h2>' in r for r in result[-3:]):
                    result.append(f'<h2>{header}</h2>')
                    added_header = True
                break
        
        # Convert to HTML paragraphs
        lines = stripped.split('\n')
        html_parts = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip redundant headers we already added
            if re.match(r'^(Module \d|Section \d|Lab \d)', line) and len(line) < 80:
                continue
            # Bold text
            line = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
            html_parts.append(f'<p>{line}</p>')
        
        if html_parts:
            result.append('\n'.join(html_parts))
    
    return '\n\n'.join(result)


# Import everything from v2 generator
import sys
sys.path.insert(0, BASE_DIR)
from generate_lessons_v2 import (
    load_plan, get_all_lessons, build_page_index, get_vision_descriptions,
    get_images_per_page, generate_nav_html, PROGRESS_JS, CSS
)


def extract_and_clean_page_text(lines, start, end):
    """Extract text from a page, clean artifacts, skip VISION blocks."""
    result = []
    in_vision = False
    for i in range(start, end):
        line = lines[i].rstrip()
        stripped = line.strip()
        if re.match(r'^--- Page \d+ ---', stripped):
            continue
        if stripped.startswith('[VISION:'):
            in_vision = True
            if ']' in stripped[8:]:
                in_vision = False
            continue
        if in_vision:
            if stripped.endswith(']') or stripped.endswith('---]'):
                in_vision = False
            continue
        result.append(line)
    
    raw_text = '\n'.join(result)
    return clean_text(raw_text)


def text_to_html_with_headers(text, lesson_id, module_title):
    """Convert cleaned text to HTML with section headers."""
    return detect_section_headers(text, lesson_id, module_title)


def generate_interleaved_content(lines, page_index, page_start, page_end, 
                                  images_per_page, visions, lesson_id, module_title):
    """Generate interleaved text+images HTML with cleaned text and headers."""
    parts = []
    
    for pg in range(page_start, page_end + 1):
        # Add cleaned text for this page
        if pg in page_index:
            start, end = page_index[pg]
            text = extract_and_clean_page_text(lines, start, end)
            html = text_to_html_with_headers(text, lesson_id, module_title)
            if html.strip():
                parts.append(html)
        
        # Add images for this page
        if pg in images_per_page:
            imgs = images_per_page[pg]
            for idx, img_path in enumerate(imgs):
                fname = os.path.basename(img_path)
                caption = visions.get(fname, f"Page {pg}")
                
                if len(imgs) > 1:
                    if fname in visions:
                        caption = visions[fname]
                    else:
                        base_caption = visions.get(os.path.basename(imgs[0]), f"Page {pg}")
                        if idx == 0:
                            caption = f"{base_caption} (step begin)"
                        else:
                            caption = f"{base_caption} (step result)"
                
                parts.append(f'<div class="screenshot">\n  <img src="../images/{fname}" alt="{caption}">\n  <div class="caption">{caption}</div>\n</div>')
    
    return '\n\n'.join(parts)


def generate_quiz(lesson):
    title = lesson["title"]
    qs = [
        (f"What are the key concepts covered in this lesson about {title}?", "Review the sections above for the main topics, step-by-step procedures, and important configuration details."),
        ("How does this topic relate to AVEVA System Platform?", "This is part of the InTouch HMI layer, which integrates with Application Server's Galaxy for a complete visualization solution."),
    ]
    items = []
    for i, (q, a) in enumerate(qs, 1):
        items.append(f'  <details>\n    <summary>Q{i}: {q}</summary>\n    <p class="answer">{a}</p>\n  </details>')
    return f'<div class="quiz">\n  <h3>Knowledge Check</h3>\n{chr(10).join(items)}\n</div>'


def generate_lesson_html(lesson, all_lessons, plan, body_content, quiz_html):
    idx = next(i for i, l in enumerate(all_lessons) if l["id"] == lesson["id"])
    prev_lesson = all_lessons[idx - 1] if idx > 0 else None
    next_lesson = all_lessons[idx + 1] if idx < len(all_lessons) - 1 else None
    nav_dropdown = generate_nav_html(lesson, all_lessons, plan)
    total = len(all_lessons)
    pg_range = f"Pages {lesson['page_start']}–{lesson['page_end']}"

    prev_link = f'<a href="{prev_lesson["filename"]}">&larr; {prev_lesson["title"]}</a>' if prev_lesson else '&larr; Start'
    next_link = f'<a href="{next_lesson["filename"]}">{next_lesson["title"]} &rarr;</a>' if next_lesson else 'End &rarr;'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lesson {lesson['id']}: {lesson['title']}</title>
<style>
{CSS}
</style>
</head>
<body>

<nav>
  {prev_link} &nbsp;|&nbsp; {next_link}
</nav>

{nav_dropdown}

<h1>Lesson {lesson['id']}: {lesson['title']}</h1>
<p class="page-ref">Module {lesson['_module']} — {lesson['_module_title']} | {pg_range}</p>

{body_content}

{quiz_html}

<p class="source">Module {lesson['_module']} — {lesson['_module_title']}. AVEVA InTouch for System Platform 2023 Training.</p>
<p class="source">Next: {"Lesson " + next_lesson["id"] + " — " + next_lesson["title"] if next_lesson else "End of course"}</p>

<script>
{PROGRESS_JS}
</script>
</body>
</html>"""


def main():
    plan = load_plan()
    all_lessons = get_all_lessons(plan)

    print("Loading complete.md...")
    page_index, lines = build_page_index(COMPLETE_MD)
    print(f"  {len(lines)} lines, {len(page_index)} pages indexed")

    print("Loading vision descriptions...")
    visions = get_vision_descriptions(COMPLETE_MD)
    print(f"  {len(visions)} vision descriptions found")

    print(f"Generating {len(all_lessons)} lessons (cleaned text + headers)...")

    for lesson in all_lessons:
        images_per_page = get_images_per_page(IMAGES_DIR, lesson["page_start"], lesson["page_end"])
        total_imgs = sum(len(v) for v in images_per_page.values())

        body_content = generate_interleaved_content(
            lines, page_index, lesson["page_start"], lesson["page_end"],
            images_per_page, visions, lesson["id"], lesson["_module_title"]
        )

        quiz_html = generate_quiz(lesson)
        html = generate_lesson_html(lesson, all_lessons, plan, body_content, quiz_html)

        out_path = os.path.join(LESSONS_DIR, lesson["filename"])
        with open(out_path, 'w') as f:
            f.write(html)

        print(f"  {lesson['id']}: {lesson['title']} ({total_imgs} images)")

    print(f"\nDone! {len(all_lessons)} lessons generated with cleaned text.")


if __name__ == "__main__":
    main()
