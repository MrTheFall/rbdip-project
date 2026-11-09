"""ЛР4: модуль review не должен зависеть от внутренностей модуля order.

Правило повторяет ArchUnit-гейт Java-варианта: ни один файл из
`app/review` не может импортировать order-код напрямую.
"""
import ast
from pathlib import Path

REVIEW_DIR = Path(__file__).resolve().parent.parent / "app" / "review"
FORBIDDEN_MODULES = {"app.models", "app.services", "app.routes"}
ORDER_INTERNALS = {"Order", "OrderItem", "Customer", "OrderService", "OrderRepository"}


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, None
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                yield module, alias.name


def test_review_module_does_not_depend_on_order():
    violations = []
    for path in sorted(REVIEW_DIR.rglob("*.py")):
        for module, imported_name in _imports(path):
            if any(module == m or module.startswith(m + ".") for m in FORBIDDEN_MODULES):
                violations.append(f"{path.name}: import {module}")
            if imported_name in ORDER_INTERNALS:
                violations.append(f"{path.name}: from {module} import {imported_name}")
    assert violations == [], f"review снова зависит от order: {violations}"
