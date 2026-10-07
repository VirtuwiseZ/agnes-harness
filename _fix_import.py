import io

path = r'E:\agh-test3\node2b_main_solve.py'
data = io.open(path, encoding='utf-8').read()

old_block = (
    "HERE = os.path.dirname(os.path.abspath(__file__))\n"
    "sys.path.insert(0, HERE)\n"
    "import artillery_model"
)
new_block = (
    "HERE = os.path.dirname(os.path.abspath(__file__))\n"
    "sys.path.insert(0, HERE)\n"
    "sys.path.insert(0, os.path.join(HERE, 'program-design', 'runtime'))\n"
    "import artillery_model"
)

if old_block in data:
    data = data.replace(old_block, new_block)
    io.open(path, 'w', encoding='utf-8').write(data)
    print('replaced ok')
else:
    print('pattern not found')
