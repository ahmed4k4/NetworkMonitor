import os
import re

# Search for hardcoded values in API responses
patterns = [
    r'"traffic":\s*0',
    r'"percentage":\s*0',
    r'"connections":\s*0',
    r'device_id.*=.*a\.name',
    r'f\.device_id.*=.*a\.name',
]

for root, dirs, files in os.walk('.'):
    if '.venv' in root or 'node_modules' in root or '.next' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    for pattern in patterns:
                        matches = list(re.finditer(pattern, content, re.IGNORECASE))
                        if matches:
                            for m in matches[:3]:
                                start = max(0, m.start() - 100)
                                end = min(len(content), m.end() + 100)
                                context = content[start:end].replace('\n', ' ')
                                print(f'{path}: {pattern}')
                                print(f'  Context: ...{context}...')
                                print()
            except:
                pass