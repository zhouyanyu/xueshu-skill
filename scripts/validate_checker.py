"""Focused structural regression checks; creates only temporary Wiki fixtures."""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path

skill = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_wiki", skill / "scripts" / "check_wiki.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

unit = {"id": "u001", "title": "测试章", "status": "completed",
        "source": "原文/u001.md", "note": "章节笔记/001.md",
        "paragraphs": 2, "read_ranges": [[1, 2]], "extra_anchors": ["n001"]}
base = {"book": "测试材料", "units": [unit]}
with tempfile.TemporaryDirectory(prefix="xueshu-", dir=Path(__file__).parent) as temp:
    root = Path(temp)
    (root / "原文").mkdir()
    (root / "章节笔记").mkdir()
    (root / "阅读首页.md").write_text("# 阅读首页\n\n[第一章](章节笔记/001.md)\n", encoding="utf-8")
    source = '# 测试章\n\n<a id="p0001"></a>\n前提。\n\n<a id="p0002"></a>\n结论。\n\n<a id="n001"></a>\n注释。\n'
    note = '# 第一章\n\n[返回](../阅读首页.md)\n\n[前提](../原文/u001.md#p0001)支持结论，条件见[注释](../原文/u001.md#n001)。\n'

    def run(data, expected, fragment=None, src=None, complete=True):
        (root / "coverage.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        (root / "原文/u001.md").write_text(source if src is None else src, encoding="utf-8")
        (root / "章节笔记/001.md").write_text(note if fragment is None else fragment, encoding="utf-8")
        errors, _ = checker.check(root, complete)
        assert bool(errors) == expected, errors

    run(base, False)
    data = copy.deepcopy(base)
    data["units"][0]["read_ranges"] = [[1, 1]]
    run(data, True)  # Completed with missing coverage must fail.
    data["units"][0]["status"] = "partial"
    run(data, False, complete=False)
    run(data, True, complete=True)
    run(base, True, fragment=note.replace("#p0001", "#p0999"))
    run(base, True, src=source.replace('<a id="p0002"></a>', ""))
    run(base, True, src=source + '\n<a id="p0003"></a>\n未登记段落。\n')
    data = copy.deepcopy(base)
    data["units"].append(copy.deepcopy(unit))
    run(data, True)  # Duplicate IDs cannot identify progress reliably.
    data = copy.deepcopy(base)
    data["units"][0]["note"] = None
    run(data, True)
    data = copy.deepcopy(base)
    data["units"][0]["source"] = "../outside.md"
    run(data, True)
    run(base, False, fragment=note + '\n```markdown\n[示例](missing.md)\n```\n')
    run(base, True, fragment=note + '\n[断链](missing.md)\n')
print("PASS: 12 coverage, source, link and code-fence checks")
