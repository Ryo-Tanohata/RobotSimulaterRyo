# tech_tree.json と design_note.md から閲覧用の index.html を生成する
import json, pathlib, html
here = pathlib.Path(__file__).parent
tree = json.loads((here/'tech_tree.json').read_text(encoding='utf-8'))
note = (here/'design_note.md').read_text(encoding='utf-8')
tpl = (here/'viewer_template.html').read_text(encoding='utf-8')
out = tpl.replace('__TREE__', json.dumps(tree, ensure_ascii=False).replace('</', '<\\/')) \
         .replace('__NOTE__', html.escape(note))
(here/'index.html').write_text(out, encoding='utf-8')
print('ok', len(out))
