import re

with open('app/routes/web.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

matches = []
for i, line in enumerate(lines):
    for m in re.finditer(r'"""', line):
        matches.append((i+1, m.start(), line.strip()[:80]))

print(f'Total triple-quote occurrences: {len(matches)}')
print(f'Status: {"ODD - Missing closing quote" if len(matches) % 2 == 1 else "EVEN - OK"}')
print('\nLast 20 occurrences:')
for ln, col, text in matches[-20:]:
    print(f'Line {ln:4d}: {text}')
