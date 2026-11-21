#!/usr/bin/env python3
"""Локальная проверка мутационной устойчивости тестов (аналог PIT для Python).

Внедряет по одной типовой ошибке в ключевые модули и прогоняет относящиеся к
ним тесты: мутация поймана, если тесты упали. Исходный код всегда
восстанавливается.

Запуск (нужен поднятый PostgreSQL с применёнными миграциями):
    python scripts/mutation_check.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PRICING_TESTS = [
    "tests/test_pricing_characterization.py",
    "tests/reference/test_reference_pricing.py",
]
ORDER_TESTS = [
    "tests/test_order_service.py",
    "tests/reference/test_reference_orders.py",
]
REVIEW_TESTS = [
    "tests/test_review_service.py",
    "tests/test_review_module.py",
]

MUTANTS = [
    (
        "app/pricing.py",
        "BULK_DISCOUNT_RATE = 0.95",
        "BULK_DISCOUNT_RATE = 0.96",
        PRICING_TESTS,
    ),
    (
        "app/pricing.py",
        "BULK_QUANTITY_THRESHOLD = 10",
        "BULK_QUANTITY_THRESHOLD = 9",
        PRICING_TESTS,
    ),
    (
        "app/pricing.py",
        "LARGE_ORDER_THRESHOLD = 1000",
        "LARGE_ORDER_THRESHOLD = 900",
        PRICING_TESTS,
    ),
    (
        "app/pricing.py",
        '"vip": 0.9',
        '"vip": 0.91',
        PRICING_TESTS,
    ),
    (
        "app/pricing.py",
        "total = max(total, 0)",
        "total = max(total, -1)",
        PRICING_TESTS,
    ),
    (
        "app/pricing.py",
        'if item["quantity"] > BULK_QUANTITY_THRESHOLD:',
        'if item["quantity"] >= BULK_QUANTITY_THRESHOLD:',
        PRICING_TESTS,
    ),
    (
        "app/services.py",
        "if quantity <= 0:",
        "if quantity < 0:",
        ORDER_TESTS,
    ),
    (
        "app/services.py",
        'status="new"',
        'status="old"',
        ORDER_TESTS,
    ),
    (
        "app/services.py",
        'payload.get("customer_type", "regular")',
        'payload.get("customer_type", "vip")',
        ORDER_TESTS,
    ),
    (
        "app/services.py",
        'coupon_code=payload.get("coupon_code"),',
        'coupon_code=payload.get("coupon_code", "SAVE10"),',
        ORDER_TESTS,
    ),
    (
        "app/services.py",
        "first_name, last_name = split_customer_name(full_name)",
        "first_name, last_name = full_name, None",
        ORDER_TESTS,
    ),
    (
        "app/review/service.py",
        "author_name=author_name",
        'author_name="anonymous"',
        REVIEW_TESTS,
    ),
]


def main():
    caught = 0
    survived = []

    for path_str, old, new, tests in MUTANTS:
        path = ROOT / path_str
        original = path.read_text(encoding="utf-8")
        if old not in original:
            print(f"SKIP     {path_str}: шаблон не найден: {old!r}")
            continue
        try:
            path.write_text(original.replace(old, new, 1), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-x", *tests],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            is_caught = result.returncode != 0
        finally:
            path.write_text(original, encoding="utf-8")

        if is_caught:
            caught += 1
            print(f"CAUGHT   {path_str}: {old!r} -> {new!r}")
        else:
            survived.append((path_str, old, new))
            print(f"SURVIVED {path_str}: {old!r} -> {new!r}")

    total = caught + len(survived)
    score = 100.0 * caught / total if total else 0.0
    print(f"\nmutation score: {caught}/{total} = {score:.0f}%")
    if survived:
        print("Выжившие мутации:", survived, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
