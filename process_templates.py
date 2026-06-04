import os, glob, re

template_dir = r'f:\Informatik\Seelauf-App\templates'
css_dir = r'f:\Informatik\Seelauf-App\static\css'
js_dir = r'f:\Informatik\Seelauf-App\static\js'

os.makedirs(css_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)

def process_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    base = os.path.splitext(os.path.basename(path))[0]
    css_file = f'static/css/{base}.css'
    js_file = f'static/js/{base}.js'
    # Ensure empty files exist
    open(os.path.join(css_dir, base + '.css'), 'a').close()
    open(os.path.join(js_dir, base + '.js'), 'a').close()
    # Replace stylesheet link
    # Match <link rel="stylesheet" href="{{ url_for('static', filename='...') }}">
    pattern_css = r'<link\s+rel=["\']stylesheet["\'][^>]*href=["\']\{\{\s*url_for\([^}]+\}\}\s*["\'][^>]*>'
    content = re.sub(pattern_css,
                     f'<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'{css_file}\') }}">',
                     content, flags=re.IGNORECASE)
    # If no stylesheet link after replacement, insert before </head>
    if not re.search(r'<link\s+rel=["\']stylesheet["\']', content, re.IGNORECASE):
        content = re.sub(r'(</head>)',
                         f'    <link rel="stylesheet" href="{{ url_for(\'static\', filename=\'{css_file}\') }}">\\n\\1',
                         content, count=1)
    # Replace script tags that point to static js
    pattern_js = r'<script\s+src=["\']\{\{\s*url_for\([^}]+\}\}\s*["\']>\s*</script>'
    content = re.sub(pattern_js,
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