"""Характеризационные тесты расчёта цены (ЛР2).

Фиксируют текущее поведение PricingCalculator на граничных и
отрицательных случаях: скидка за объём, VIP/wholesale, купоны,
отсечение отрицательного итога и порог крупного заказа.
"""
from app.pricing import PricingCalculator

calculator = PricingCalculator()


def line(price, quantity=1):
    return [{"price": price, "quantity": quantity}]


def test_regular_customer_without_discounts():
    assert calculator.calculate(line(10.0, 2)) == 20.0


def test_no_bulk_discount_at_ten_units():
    assert calculator.calculate(line(10.0, 10)) == 100.0


def test_bulk_discount_applies_above_ten_units():
    assert calculator.calculate(line(10.0, 11)) == 104.5


def test_vip_customer_gets_ten_percent_off():
    assert calculator.calculate(line(100.0), "vip") == 90.0


def test_wholesale_customer_gets_fifteen_percent_off():
    assert calculator.calculate(line(100.0), "wholesale") == 85.0


def test_unknown_customer_type_gets_no_discount():
    assert calculator.calculate(line(100.0), "platinum") == 100.0


def test_fixed_coupon_subtracts_ten():
    assert calculator.calculate(line(100.0), coupon_code="SAVE10") == 90.0


def test_percent_coupon_takes_twenty_percent_off():
    assert calculator.calculate(line(100.0), coupon_code="SAVE20PERCENT") == 80.0


def test_unknown_coupon_is_ignored():
    assert calculator.calculate(line(100.0), coupon_code="FREEBIE") == 100.0


def test_total_is_never_negative():
    assert calculator.calculate(line(5.0), coupon_code="SAVE10") == 0.0


def test_large_order_gets_two_percent_off():
    assert calculator.calculate(line(2000.0)) == 1960.0


def test_exactly_one_thousand_is_not_discounted():
    assert calculator.calculate(line(1000.0)) == 1000.0


def test_coupon_applies_after_customer_discount():
    assert calculator.calculate(line(100.0), "vip", "SAVE20PERCENT") == 72.0


def test_large_order_discount_applies_after_coupon():
    assert calculator.calculate(line(1500.0), coupon_code="SAVE10") == 1460.2


def test_result_is_rounded_to_two_decimals():
    assert calculator.calculate(line(9.99), "vip") == 8.99


def test_empty_order_costs_nothing():
    assert calculator.calculate([]) == 0.0
