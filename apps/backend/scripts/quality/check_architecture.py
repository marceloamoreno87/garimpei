"""Bounded AST checks; DI and transaction tests complement this gate."""

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/garimpei"
ALLOWED_ROOT_FILES = {"__init__.py", "main.py"}
ALLOWED_DIRECTORIES = {"config", "domain", "usecase", "infra"}


def check_file(path: Path) -> list[str]:
    relative = path.relative_to(SOURCE)
    errors: list[str] = []
    if relative.parts[0] not in ALLOWED_DIRECTORIES and str(relative) not in ALLOWED_ROOT_FILES:
        errors.append(f"{relative}: module outside approved architecture")
    tree = ast.parse(path.read_text(), filename=str(relative))
    for node in ast.walk(tree):
        errors.extend(check_node(relative, node))
    return errors + check_depth(relative, tree, 0) + check_import_effects(relative, tree)


def check_node(relative: Path, node: ast.AST) -> list[str]:
    errors: list[str] = []
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"import_module", "exec_module"}
    ):
        errors.append(
            f"{relative}:{node.lineno}: dynamic imports require an inspected framework registry"
        )
    if (
        isinstance(node, ast.Attribute)
        and node.attr in {"environ", "getenv", "putenv"}
        and str(relative) != "config/env.py"
    ):
        errors.append(f"{relative}:{node.lineno}: environment access belongs in config/env.py")
    if isinstance(node, ast.Name) and node.id == "Any":
        errors.append(f"{relative}:{node.lineno}: explicit types required instead of Any")
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and relative.parts[0] == "usecase"
        and node.func.id.endswith(("Adapter", "Probe", "Gateway", "Repository"))
    ):
        errors.append(f"{relative}:{node.lineno}: concrete adapter construction belongs in main.py")
    if (
        relative.name.endswith("handler.py")
        and isinstance(node, ast.Try)
        and "http" in relative.parts
    ):
        errors.append(
            f"{relative}:{node.lineno}: HTTP exceptions belong to central error middleware"
        )
    return errors


def check_import_effects(relative: Path, node: ast.AST) -> list[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    if isinstance(node, ast.If) and "__name__" in ast.unparse(node.test):
        return []
    errors: list[str] = []
    forbidden = {
        "open",
        "print",
        "exec",
        "eval",
        "__import__",
        "connect",
        "execute",
        "urlopen",
        "Popen",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "defer",
    }
    if isinstance(node, ast.Call):
        name = (
            node.func.id
            if isinstance(node.func, ast.Name)
            else node.func.attr
            if isinstance(node.func, ast.Attribute)
            else ""
        )
        if name in forbidden:
            errors.append(f"{relative}:{node.lineno}: I/O at import time is forbidden")
    return errors + [
        error
        for child in ast.iter_child_nodes(node)
        for error in check_import_effects(relative, child)
    ]


def check_depth(relative: Path, node: ast.AST, depth: int) -> list[str]:
    blocks = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.AsyncFor)
    next_depth = depth + 1 if isinstance(node, blocks) else depth
    if next_depth > 2:
        return [f"{relative}:{getattr(node, 'lineno', 0)}: more than two nested blocks"]
    return [
        error
        for child in ast.iter_child_nodes(node)
        for error in check_depth(
            relative, child, 0 if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else next_depth
        )
    ]


def check_registry() -> list[str]:
    records = json.loads((ROOT / "quality/entrypoints.json").read_text())
    return [
        f"Registry: unverified entrypoint {record['symbol']}"
        for record in records
        if not record["reason"]
        or not (ROOT / record["path"]).is_file()
        or not (ROOT / record["consumer"]).is_file()
    ]


def main() -> int:
    files = sorted(SOURCE.rglob("*.py"))
    errors = [error for path in files for error in check_file(path)] + check_registry()
    print(f"Architecture: {len(files)} source files; {len(errors)} violations")
    for error in errors:
        print(error)
    return 1 if errors or not files else 0


if __name__ == "__main__":
    sys.exit(main())
