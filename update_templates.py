import os, glob, re

template_dir = r'f:\Informatik\Seelauf-App\templates'
css_dir = r'f:\Informatik\Seelauf-App\static\css'
js_dir = r'f:\Informatik\Seelauf-App\static\js'

os.makedirs(css_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)

def process_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Determine base name without extension
    base = os.path.splitext(os.path.basename(path))[0]
    css_file = f'static/css/{base}.css'
    js_file = f'static/js/{base}.js'
    # Ensure empty files exist
    open(os.path.join(css_dir, base + '.css'), 'a').close()
    open(os.path.join(js_dir, base + '.js'), 'a').close()
    # Replace any existing stylesheet link with our pattern
    # Pattern: <link rel="stylesheet" href="{{ url_for('static', filename='...css') }}">
    # We'll replace all occurrences
    content = re.sub(r'<link\s+rel=["\']stylesheet["\']\s+href=["\']\{\{\s*url_for\([^}]+\}\}\s*["\']>',
                     f'<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'{css_file}\') }}">',
                     content, flags=re.IGNORECASE)
    # If no stylesheet link after replacement, insert before </head>
    if not re.search(r'<link\s+rel=["\']stylesheet["\']', content, re.IGNORECASE):
        content = re.sub(r'(</head>)',
                         f'    <link rel="stylesheet" href="{{ url_for(\'static\', filename=\'{css_file}\') }}">\\n\\1',
                         content, count=1)
    # Replace any existing script tag that src points to static js with our pattern
    # We'll replace all <script src="{{ url_for('static', filename='...js') }}"></script>
    content = re.sub(r'<script\s+src=["\']\{\{\s*url_for\([^}]+\}\}\s*["\']>\s*</script>',
                     f'<script src="{{ url_for(\'static\', filename=\'{js_file}\') }}"></script>',
                     content, flags=re.IGNORECASE)
    # Ensure a script tag just before </body>
    if not re.search(r'<script\s+src', content, re.IGNORECASE):
        content = re.sub(r'(</body>)',
                         f'    <script src="{{ url_for(\'static\', filename=\'{js_file}\') }}"></script>\\n\\1',
                         content, count=1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

for tmpl in glob.glob(os.path.join(template_dir, '*.html')):
    process_template(tmpl)
    print(f'Processed {tmpl}')