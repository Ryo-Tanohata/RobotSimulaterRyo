# tech_tree.json と design_note.md から閲覧用の index.html を生成する
import json, pathlib
here = pathlib.Path(__file__).parent
tree = json.loads((here/'tech_tree.json').read_text(encoding='utf-8'))
note = (here/'design_note.md').read_text(encoding='utf-8')
tpl = (here/'viewer_template.html').read_text(encoding='utf-8')
# どちらも JSON で埋め込む（script の中は文字参照が解かれないので html.escape は使わない。</ だけ <\/ にする）
js = lambda x: json.dumps(x, ensure_ascii=False).replace('</', '<\\/')
out = tpl.replace('__TREE__', js(tree)).replace('__NOTE__', js(note))
(here/'index.html').write_text(out, encoding='utf-8')
print('ok', len(out))
