import io

path = r'E:\agh-test3\node2b_verification_boundary.py'
data = io.open(path, encoding='utf-8').read()

old = 'with open(os.path.join(HERE, "boundary_spec_artillery.json"), "w", encoding="utf-8") as f:'
new = 'with open(os.path.join(HERE, "program-design", "runtime", "boundary_spec_artillery.json"), "w", encoding="utf-8") as f:'

if old in data:
    data = data.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(data)
    print('fixed ok')
else:
    print('pattern not found')
