#!/usr/bin/env python3
"""
Script to update all HTML files with theme.css link and simplified Tailwind config
"""

import os
import re
from pathlib import Path

# Define the patterns to search for and replace
OLD_TAILWIND_CONFIG = r'''  <script>
    tailwind\.config = \{
      darkMode: 'class',
      theme: \{
        extend: \{
          colors: \{[^}]+\},
          fontFamily: \{
            display: \['Syne', 'sans-serif'\],
            body: \['Space Grotesk', 'sans-serif'\],
            mono: \['JetBrains Mono', 'monospace'\],
          \},
        \}
      \}
    \}
  </script>'''

NEW_TAILWIND_CONFIG = '''  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            display: ['Syne', 'sans-serif'],
            body: ['Space Grotesk', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          },
        }
      }
    }
  </script>'''

OLD_CSS_LINK = r'  <link rel="icon" type="image/svg\+xml" href="assets/favicon\.svg">\n  <script src="https://cdn\.tailwindcss\.com"></script>'
NEW_CSS_LINK = '''  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
  <link rel="stylesheet" href="assets/theme.css">
  <script src="https://cdn.tailwindcss.com"></script>'''

def update_html_file(filepath):
    """Update a single HTML file"""
    print(f"Processing: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Update CSS link
    content = re.sub(OLD_CSS_LINK, NEW_CSS_LINK, content)

    # Update Tailwind config
    content = re.sub(OLD_TAILWIND_CONFIG, NEW_TAILWIND_CONFIG, content, flags=re.DOTALL)

    # Remove old light theme styles if present
    old_style_pattern = r'    ::-webkit-scrollbar[^<]+</style>\n\n    /\* Light theme colors \*/\n    \.light \{[^}]+\}\n  </style>'
    content = re.sub(old_style_pattern, '  </style>', content, flags=re.DOTALL)

    # Simplify style section
    old_style_section = r'  <style>\n    @layer base \{[^}]+\}\n    ::-webkit-scrollbar[^}]+\}[^}]+\}[^}]+\}\n\n    /\* Light theme colors \*/\n    \.light \{[^}]+\}\n  </style>'
    new_style_section = '''  <style>
    @layer base {
      html, body { margin: 0; padding: 0; }
      body { overscroll-behavior: none; }
    }
  </style>'''
    content = re.sub(old_style_section, new_style_section, content, flags=re.DOTALL)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Updated {filepath}")
        return True
    else:
        print(f"  [-] No changes needed for {filepath}")
        return False

def main():
    web_dir = Path(__file__).parent.parent / 'web'
    html_files = list(web_dir.glob('*.html'))

    print(f"Found {len(html_files)} HTML files")
    print("-" * 50)

    updated_count = 0
    for html_file in html_files:
        if update_html_file(html_file):
            updated_count += 1

    print("-" * 50)
    print(f"Updated {updated_count} out of {len(html_files)} files")

if __name__ == '__main__':
    main()
