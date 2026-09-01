"""Baseline behavior tests for pricing. Do not edit.

Only covers the simple, documented path. Edge cases (bulk discounts,
VIP/wholesale rates, coupons, the >1000 threshold) are intentionally
left uncovered — writing characterization tests for them is part of
lab 2.
"""
from app.services import calculate_order_total


def test_regular_customer_no_discount():
    items = [{"price": 10.0, "quantity": 2}]
    assert calculate_order_total(items) == 20.0
