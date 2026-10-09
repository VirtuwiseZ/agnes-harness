import io

p = 'program-design/hooks/make_report_figures.py'
block_path = 'dev-notes/self-tests/03/figures_interactive_test/new_interactive_live_block.txt'

with open(p, 'r', encoding='utf-8', newline='') as f:
    text = f.read()

lines = text.split('\r\n')
assert lines[874] == '    js_div_id = div_id', repr(lines[874])
assert lines[941] == '    )', repr(lines[941])
assert lines[942] == '', repr(lines[942])
assert 'inject = controls_block' in lines[943], repr(lines[943])

with open(block_path, 'r', encoding='utf-8', newline='') as f:
    new_block_raw = f.read()

# new_block_raw was written with LF line endings; split and rejoin with CRLF.
new_block_lines = new_block_raw.split('\n')
# The write tool may have produced a trailing newline; drop a single trailing empty
# element that would otherwise add an extra blank CRLF line at the end of the splice.
if new_block_lines and new_block_lines[-1] == '':
    new_block_lines = new_block_lines[:-1]

# Replace lines[874:942] (i.e. indices 874..941 inclusive) with new_block_lines.
new_lines = lines[:874] + new_block_lines + lines[942:]
new_text = '\r\n'.join(new_lines)

with open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(new_text)

print('OK. lines before:', len(lines), 'lines after:', len(new_lines),
      'delta:', len(new_lines) - len(lines))
