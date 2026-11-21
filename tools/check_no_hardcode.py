"""Scan chonoi/sim Python files for numeric tuning values outside the contract."""

import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
STRUCTURAL = {0, 1, -1, 0.0, 1.0, 360}  # 360: vòng góc (heading % 360), không phải số tuning
ALLOW_MARKER = "# allow-hardcode"


def tuning_numbers(value):
    """Return every numeric (non-boolean) value nested in the tuning contract."""
    found = set()
    if isinstance(value, bool):
        return found
    if isinstance(value, (int, float)):
        found.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            found.update(tuning_numbers(item))
    elif isinstance(value, list):
        for item in value:
            found.update(tuning_numbers(item))
    return found


def annotation_nodes(tree):
    """Collect AST nodes that belong to annotations, which may contain numeric types."""
    ignored = set()

    def collect(node):
        if node is not None:
            ignored.update(id(child) for child in ast.walk(node))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            collect(node.returns)
            for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
                collect(arg.annotation)
            if node.args.vararg:
                collect(node.args.vararg.annotation)
            if node.args.kwarg:
                collect(node.args.kwarg.annotation)
        elif isinstance(node, ast.AnnAssign):
            collect(node.annotation)
    return ignored


def scan_file(path, contract_numbers):
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source, filename=str(path))
    ignored_annotations = annotation_nodes(tree)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    findings = []

    for node in ast.walk(tree):
        if id(node) in ignored_annotations:
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            parent = parents.get(node)
            if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, (ast.USub, ast.UAdd)):
                continue
            value = node.value
        elif (isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd))
              and isinstance(node.operand, ast.Constant)
              and isinstance(node.operand.value, (int, float))
              and not isinstance(node.operand.value, bool)):
            value = -node.operand.value if isinstance(node.op, ast.USub) else node.operand.value
        else:
            continue

        line = node.lineno
        if ALLOW_MARKER in lines[line - 1]:
            continue
        if value in STRUCTURAL or value in contract_numbers:
            continue
        findings.append((line, value, "numeric literal is not a structural constant or contract tuning value"))

    return findings


def main():
    try:
        with (ROOT / "game.contract.json").open(encoding="utf-8") as f:
            contract = json.load(f)
        contract_numbers = tuning_numbers(contract.get("tuning", {}))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"check_no_hardcode: cannot read contract: {exc}", file=sys.stderr)
        return 1

    files = sorted((ROOT / "chonoi" / "sim").glob("*.py"), key=lambda p: p.as_posix())
    findings = []
    for path in files:
        try:
            findings.extend((path.relative_to(ROOT).as_posix(), *item)
                            for item in scan_file(path, contract_numbers))
        except (OSError, SyntaxError, UnicodeError) as exc:
            print(f"{path.relative_to(ROOT).as_posix()}: cannot scan file: {exc}", file=sys.stderr)
            return 1

    if findings:
        for filename, line, value, reason in findings:
            print(f"{filename}:{line}: {value} - {reason}")
        return 1
    print("OK: no suspicious numeric literals in chonoi/sim/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
