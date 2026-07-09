#!/usr/bin/env python3
"""Auto-generate InTouch training lessons from complete.md + images."""
import json
import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
LESSONS_DIR = os.path.join(BASE_DIR, "lessons")
PLAN_FILE = os.path.join(BASE_DIR, "lesson_plan.json")

# Read the complete.md
COMPLETE_MD = "/home/eng_zaki/.hermes/skills/software-development/aveva-intouch/references/aveva_intouch_complete.md"

CSS = """  body { font-family: Georgia, serif; max-width: 900px; margin: 2em auto; padding: 0 1em; line-height: 1.7; color: #1a1a1a; }
  h1 { font-size: 1.8em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }
  h2 { font-size: 1.3em; color: #2c5f2d; margin-top: 1.5em; }
  h3 { font-size: 1.1em; color: #555; }
  .key-concept { background: #f0f7f0; border-left: 4px solid #2c5f2d; padding: 1em; margin: 1em 0; }
  .pitfall { background: #fff3f3; border-left: 4px solid #c0392b; padding: 1em; margin: 1em 0; }
  .lab { background: #f0f4ff; border-left: 4px solid #2c3e50; padding: 1em; margin: 1em 0; }
  .tip { background: #fffde7; border-left: 4px solid #f39c12; padding: 1em; margin: 1em 0; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { border: 1px solid #ddd; padding: 0.5em; text-align: left; }
  th { background: #f5f5f5; }
  code { background: #f4f4f4; padding: 0.1em 0.4em; font-size: 0.95em; }
  .screenshot { text-align: center; margin: 1.5em 0; }
  .screenshot img { max-width: 100%; border: 1px solid #ccc; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  .screenshot .caption { font-size: 0.85em; color: #666; font-style: italic; margin-top: 0.5em; }
  .quiz { background: #fffde7; border: 1px solid #f0e68c; padding: 1em; margin: 2em 0; }
  .quiz h3 { margin-top: 0; }
  .answer { color: #2c5f2d; font-weight: bold; }
  nav { margin-bottom: 2em; font-size: 0.9em; }
  nav a { color: #2c5f2d; }
  .source { font-size: 0.85em; color: #777; font-style: italic; }
  .page-ref { font-size: 0.8em; color: #999; }
  .checkbox-label { cursor: pointer; }
  .checkbox-label input { margin-right: 0.3em; }
  #progress-text { color: #2c5f2d; font-weight: bold; }"""

PROGRESS_JS = """
function saveProgress() {
  var checks = {};
  document.querySelectorAll('input[data-lesson]').forEach(function(cb) {
    checks[cb.dataset.lesson] = cb.checked;
  });
  try {
    localStorage.setItem('intouch-lesson-progress', JSON.stringify(checks));
  } catch(e) {}
  updateProgressText();
}

function loadProgress() {
  var data = null;
  try {
    data = localStorage.getItem('intouch-lesson-progress');
  } catch(e) {}
  if (!data) {
    updateProgressText();
    return;
  }
  try {
    var checks = JSON.parse(data);
    document.querySelectorAll('input[data-lesson]').forEach(function(cb) {
      if (checks[cb.dataset.lesson]) {
        cb.checked = true;
      }
    });
  } catch(e) {}
  updateProgressText();
}

function updateProgressText() {
  var total = document.querySelectorAll('input[data-lesson]').length;
  var done = document.querySelectorAll('input[data-lesson]:checked').length;
  var el = document.getElementById('progress-text');
  if (el) el.textContent = done + ' / ' + total + ' completed';
}

document.addEventListener('DOMContentLoaded', loadProgress);
"""


def load_plan():
    with open(PLAN_FILE) as f:
        return json.load(f)


def get_all_lessons(plan):
    """Flatten all lessons across modules."""
    lessons = []
    for mod in plan["modules"]:
        for les in mod["lessons"]:
            les["_module"] = mod["module"]
            les["_module_title"] = mod["title"]
            lessons.append(les)
    return lessons


def build_page_index(complete_md_path):
    """Build a dict: page_number -> (start_line, end_line) in complete.md."""
    with open(complete_md_path) as f:
        lines = f.readlines()

    page_starts = {}
    for i, line in enumerate(lines):
        m = re.match(r'^--- Page (\d+) ---', line)
        if m:
            pg = int(m.group(1))
            page_starts[pg] = i

    sorted_pgs = sorted(page_starts.keys())
    page_index = {}
    for idx, pg in enumerate(sorted_pgs):
        start = page_starts[pg]
        if idx + 1 < len(sorted_pgs):
            end = page_starts[sorted_pgs[idx + 1]]
        else:
            end = len(lines)
        page_index[pg] = (start, end)

    return page_index, lines


def extract_lesson_content(lines, page_index, page_start, page_end):
    """Extract text content for a lesson's page range, skipping VISION blocks.
    
    VISION blocks are multi-line: [VISION: ... ] where ] is at end of a line.
    Must skip the entire block, not just the first line.
    """
    all_text = []
    in_vision = False
    
    for pg in range(page_start, page_end + 1):
        if pg not in page_index:
            continue
        start, end = page_index[pg]
        page_lines = lines[start:end]

        # Add page marker
        all_text.append(f"\n--- Page {pg} ---\n")

        for line in page_lines:
            stripped = line.strip()
            
            # Skip --- Page N --- markers (we add our own)
            if re.match(r'^--- Page \d+ ---', stripped):
                continue
            
            # Handle multi-line VISION blocks
            if stripped.startswith('[VISION:'):
                in_vision = True
                # Check if the block closes on the same line
                if ']' in stripped[8:]:  # after [VISION:
                    in_vision = False
                continue
            
            if in_vision:
                # Check if this line closes the VISION block
                if stripped.endswith(']') or stripped.endswith('---]'):
                    in_vision = False
                continue
            
            all_text.append(line.rstrip())

    return '\n'.join(all_text)


def get_images_for_lesson(images_dir, page_start, page_end):
    """Get sorted list of image files for the given page range."""
    all_images = sorted(glob.glob(os.path.join(images_dir, "page_*.*")))
    result = []
    for img_path in all_images:
        fname = os.path.basename(img_path)
        m = re.match(r'page_(\d+)', fname)
        if m:
            pg = int(m.group(1))
            if page_start <= pg <= page_end:
                result.append(img_path)
    return result


def get_vision_descriptions(complete_md_path, page_start, page_end):
    """Extract VISION descriptions for images in the page range.
    
    VISION blocks are multi-line with two formats:
    1. [VISION: ### page_NNNN.png — Title ...]
    2. [VISION: ### page_NNNN.png\n**Title**\n- Content ...]
    
    They start with [VISION: and end with ] at end of a line.
    """
    with open(complete_md_path) as f:
        content = f.read()

    visions = {}
    
    # Find all VISION blocks (multi-line)
    vision_pattern = re.compile(r'\[VISION:\s*(.*?)(?:\]|\-\-\-\])', re.DOTALL)
    
    for m in vision_pattern.finditer(content):
        block = m.group(0)
        header = m.group(1)
        
        # Extract filename from header
        fname_match = re.search(r'page_(\d+)(?:_(\d+))?\.(\w+)', header)
        if not fname_match:
            continue
        
        pg_num = fname_match.group(1)
        sub_idx = fname_match.group(2)
        ext = fname_match.group(3)
        
        if sub_idx:
            filename = f"page_{pg_num}_{sub_idx}.{ext}"
        else:
            filename = f"page_{pg_num}.{ext}"
        
        # Try to extract title from header line (after em dash or " - " separator)
        title = None
        # Only match em dash or " - " (space-dash-space), not hyphens inside words
        title_match = re.search(r'[—–]\s*(.+?)(?:\n|$)', header)
        if not title_match:
            title_match = re.search(r'\s+-\s+(.+?)(?:\n|$)', header)
        if title_match:
            title = title_match.group(1).strip()
        
        # If no title on first line, look at subsequent lines in the block
        if not title:
            lines = block.split('\n')
            for line in lines[1:]:
                stripped = line.strip()
                # Skip empty lines and lines that are just formatting
                if not stripped or stripped.startswith('```'):
                    continue
                # Look for bold title: **Title**
                bold_match = re.match(r'\*\*(.+?)\*\*', stripped)
                if bold_match:
                    title = bold_match.group(1)
                    break
                # Look for descriptive text after a dash
                dash_match = re.match(r'^[-*]\s+(.+)', stripped)
                if dash_match and len(dash_match.group(1)) > 10:
                    title = dash_match.group(1)[:100]
                    break
                # Use first non-empty line
                if not stripped.startswith('[') and not stripped.startswith('#'):
                    title = stripped[:100]
                    break
        
        if not title:
            title = f"Page {pg_num}"
        
        # Clean markdown
        title = re.sub(r'\*\*([^*]+)\*\*', r'\1', title)
        title = title.strip()
        # Remove trailing ** artifacts (markdown bold remnant)
        title = re.sub(r'\*+$', '', title).strip()
        # Remove leading/trailing quotes
        title = title.strip('"').strip("'")
        
        visions[filename] = title

    return visions


def clean_text_for_html(text):
    """Convert markdown-like text to HTML paragraphs."""
    # Remove vision blocks
    text = re.sub(r'\[VISION:.*?(?:---\]|\])', '', text, flags=re.DOTALL)

    paragraphs = []
    current = []

    for line in text.split('\n'):
        stripped = line.strip()
        if stripped == '':
            if current:
                paragraphs.append(' '.join(current))
                current = []
        elif stripped.startswith('--- Page'):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            # Don't include page markers in body
        else:
            current.append(stripped)

    if current:
        paragraphs.append(' '.join(current))

    html_parts = []
    for p in paragraphs:
        if not p.strip():
            continue
        # Detect section headers
        if re.match(r'^(Module \d|Section \d|Lab \d)', p) and len(p) < 100:
            continue  # Skip redundant headers
        # Bold text
        p = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', p)
        # Code
        p = re.sub(r'`([^`]+)`', r'<code>\1</code>', p)
        html_parts.append(f'<p>{p}</p>')

    return '\n'.join(html_parts)


def generate_nav_html(lesson, all_lessons, plan):
    """Generate the dropdown navigation menu."""
    total = len(all_lessons)
    items = []
    for mod in plan["modules"]:
        items.append(f'<strong>Module {mod["module"]} &#8212; {mod["title"]}</strong><br>')
        for les in mod["lessons"]:
            checked = ' checked' if les["id"] == lesson["id"] else ''
            active = ' style="font-weight:bold;"' if les["id"] == lesson["id"] else ''
            items.append(
                f'<label style="cursor:pointer;display:block;margin:0.1em 0;">'
                f'<input type="checkbox" data-lesson="{les["id"]}"{checked} onchange="saveProgress()"> '
                f'<a href="{les["filename"]}"{active}>{les["id"]}: {les["title"]}</a></label>'
            )

    nav_content = '\n'.join(items)
    return f"""<nav style="margin-bottom:1.5em;">
<details style="background:#f5f5f5;padding:0.8em;border-radius:6px;border:1px solid #ddd;margin-bottom:1.5em;">
<summary style="cursor:pointer;font-weight:bold;font-size:1.1em;color:#2c5f2d;">&#128218; All Lessons</summary>
<div style="margin-top:0.8em;line-height:1.8;max-height:70vh;overflow-y:auto;">
<div style="margin-bottom:0.5em;padding:0.5em;background:#e8f5e9;border-radius:4px;">
<strong style="color:#2c5f2d;">&#9989; Progress: <span id="progress-text">0 / {total} completed</span></strong>
</div>
{nav_content}
</div>
</details>
</nav>"""


def generate_quiz(lesson):
    """Generate a basic quiz section."""
    module = lesson["_module"]
    title = lesson["title"]

    # Generate context-aware quiz questions
    quizzes = {
        "L01": [
            ("What does the System Platform course cover?", "AVEVA System Platform — Galaxy architecture, Application Server, InTouch HMI, device integration, alarms, history, scripting, and security."),
            ("What is InTouch HMI used for?", "Creating visualization screens (graphics) that display real-time data from the plant floor for operator interaction."),
        ],
        "L02": [
            ("What is a Galaxy in AVEVA System Platform?", "The Galaxy is the central object-oriented database that stores all system objects, templates, instances, and configurations."),
            ("What is the role of Application Server?", "Application Server is the backend engine that hosts the Galaxy, processes automation logic, and manages communication with field devices."),
        ],
    }

    default_qs = [
        (f"What are the key concepts covered in this lesson about {title}?", "Review the sections above for the main topics, step-by-step procedures, and important configuration details."),
        ("How does this topic relate to AVEVA System Platform?", "This is part of the InTouch HMI layer, which integrates with Application Server's Galaxy for a complete visualization solution."),
    ]

    qs = quizzes.get(lesson["id"], default_qs)

    items = []
    for i, (q, a) in enumerate(qs, 1):
        items.append(f"""  <details>
    <summary>Q{i}: {q}</summary>
    <p class="answer">{a}</p>
  </details>""")

    return f"""<div class="quiz">
  <h3>Knowledge Check</h3>
{chr(10).join(items)}
</div>"""


def generate_lesson_html(lesson, all_lessons, plan, body_content, images, visions):
    """Generate the full HTML for a lesson."""
    idx = next(i for i, l in enumerate(all_lessons) if l["id"] == lesson["id"])
    prev_lesson = all_lessons[idx - 1] if idx > 0 else None
    next_lesson = all_lessons[idx + 1] if idx < len(all_lessons) - 1 else None

    # Prev/Next nav
    prev_link = f'<a href="{prev_lesson["filename"]}">&larr; {prev_lesson["title"]}</a>' if prev_lesson else '&larr; Start'
    next_link = f'<a href="{next_lesson["filename"]}">{next_lesson["title"]} &rarr;</a>' if next_lesson else 'End &rarr;'

    nav_dropdown = generate_nav_html(lesson, all_lessons, plan)

    # Image HTML
    images_html = []
    for img_path in images:
        fname = os.path.basename(img_path)
        # Get vision description
        caption = visions.get(fname, f"Page {fname.split('_')[1].split('.')[0]}")
        # Also try with sub-index
        if caption == f"Page {fname.split('_')[1].split('.')[0]}":
            # Try base page number
            m = re.match(r'page_(\d+)', fname)
            if m:
                base = m.group(1)
                for k, v in visions.items():
                    if k.startswith(f"page_{base}"):
                        caption = v
                        break

        images_html.append(f"""<div class="screenshot">
  <img src="../images/{fname}" alt="{caption}">
  <div class="caption">{caption}</div>
</div>""")

    images_block = '\n'.join(images_html)

    # Body content
    body_html = clean_text_for_html(body_content)

    # Quiz
    quiz_html = generate_quiz(lesson)

    total = len(all_lessons)
    pg_range = f"Pages {lesson['page_start']}–{lesson['page_end']}"

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
  <a href="{prev_link}">&larr; Previous</a> &nbsp;|&nbsp;
  {"<a href='" + next_lesson["filename"] + "'>" + next_lesson["title"] + " &rarr;</a>" if next_lesson else "End &rarr;"}
</nav>

{nav_dropdown}

<h1>Lesson {lesson['id']}: {lesson['title']}</h1>
<p class="page-ref">Module {lesson['_module']} — {lesson['_module_title']} | {pg_range}</p>

{images_block}

{body_html}

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

    print(f"Loading complete.md...")
    page_index, lines = build_page_index(COMPLETE_MD)
    print(f"  {len(lines)} lines, {len(page_index)} pages indexed")

    print(f"Loading vision descriptions...")
    visions = get_vision_descriptions(COMPLETE_MD, 1, 550)
    print(f"  {len(visions)} vision descriptions found")

    print(f"Generating {len(all_lessons)} lessons...")

    for lesson in all_lessons:
        # Extract content
        content = extract_lesson_content(lines, page_index, lesson["page_start"], lesson["page_end"])

        # Get images
        images = get_images_for_lesson(IMAGES_DIR, lesson["page_start"], lesson["page_end"])

        # Generate HTML
        html = generate_lesson_html(lesson, all_lessons, plan, content, images, visions)

        # Write file
        out_path = os.path.join(LESSONS_DIR, lesson["filename"])
        with open(out_path, 'w') as f:
            f.write(html)

        img_count = len(images)
        print(f"  {lesson['id']}: {lesson['title']} ({img_count} images)")

    print(f"\nDone! {len(all_lessons)} lessons generated in {LESSONS_DIR}/")


if __name__ == "__main__":
    main()
