with open('app/routes/web.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find lines with odd number of triple quotes
odd_lines = []
for i, line in enumerate(lines):
    count = line.count('"""')
    if count % 2 == 1:
        odd_lines.append((i+1, count, line.rstrip()))

print(f'Lines with ODD triple-quote count: {len(odd_lines)}')
for ln, cnt, text in odd_lines:
    print(f'Line {ln}: {text[:100]}')
