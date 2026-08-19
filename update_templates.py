import os
import glob
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / 'templates'
STATIC_CSS_DIR = BASE_DIR / 'static' / 'css'
STATIC_JS_DIR = BASE_DIR / 'static' / 'js'

STATIC_CSS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_JS_DIR.mkdir(parents=True, exist_ok=True)

CSS_PATTERN = r'<link\s+rel=["\']stylesheet["\']\s+href=["\']\{\{\s*url_for\([^}]+\}\}\s*["\']>'
JS_PATTERN = r'<script\s+src=["\']\{\{\s*url_for\([^}]+\}\}\s*["\']>\s*</script>'


def process_template(template_path):
    """Standardisiert CSS- und JS-Links in HTML-Templates."""
    base_name = template_path.stem
    css_link = f'<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'static/css/{base_name}.css\') }}">'
    js_link = f'<script src="{{ url_for(\'static\', filename=\'static/js/{base_name}.js\') }}"></script>'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Erstelle CSS- und JS-Dateien
    (STATIC_CSS_DIR / f'{base_name}.css').touch()
    (STATIC_JS_DIR / f'{base_name}.js').touch()
    
    # Ersetze oder füge CSS-Link ein
    content = re.sub(CSS_PATTERN, css_link, content, flags=re.IGNORECASE)
    if not re.search(r'<link\s+rel=["\']stylesheet["\']', content, re.IGNORECASE):
        content = re.sub(r'(</head>)', f'    {css_link}\n\\1', content, count=1)
    
    # Ersetze oder füge JS-Link ein
    content = re.sub(JS_PATTERN, js_link, content, flags=re.IGNORECASE)
    if not re.search(r'<script\s+src', content, re.IGNORECASE):
        content = re.sub(r'(</body>)', f'    {js_link}\n\\1', content, count=1)
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    for template in TEMPLATE_DIR.glob('*.html'):
        process_template(template)
        print(f'✓ {template.name}')