"""Order pricing rules.

All discount rates and thresholds live here as named constants so that the
calculation itself contains no magic numbers.
"""

BULK_QUANTITY_THRESHOLD = 10
BULK_DISCOUNT_RATE = 0.95

CUSTOMER_DISCOUNT_RATES = {
    "vip": 0.9,
    "wholesale": 0.85,
}

FIXED_COUPON_DISCOUNTS = {
    "SAVE10": 10,
}

PERCENT_COUPON_DISCOUNTS = {
    "SAVE20PERCENT": 0.8,
}

LARGE_ORDER_THRESHOLD = 1000
LARGE_ORDER_DISCOUNT_RATE = 0.98


class PricingCalculator:
    """Calculates an order total from its line items."""

    def calculate(self, items, customer_type="regular", coupon_code=None):
        total = self._items_total(items)
        total *= CUSTOMER_DISCOUNT_RATES.get(customer_type, 1.0)
        total = self._apply_coupon(total, coupon_code)
        total = max(total, 0)
        if total > LARGE_ORDER_THRESHOLD:
            total *= LARGE_ORDER_DISCOUNT_RATE
        return round(total, 2)

    @staticmethod
    def _items_total(items):
        total = 0
        for item in items:
            line_price = item["price"] * item["quantity"]
            if item["quantity"] > BULK_QUANTITY_THRESHOLD:
                line_price *= BULK_DISCOUNT_RATE
            total += line_price
        return total

    @staticmethod
    def _apply_coupon(total, coupon_code):
        if coupon_code in FIXED_COUPON_DISCOUNTS:
            return total - FIXED_COUPON_DISCOUNTS[coupon_code]
        if coupon_code in PERCENT_COUPON_DISCOUNTS:
            return total * PERCENT_COUPON_DISCOUNTS[coupon_code]
        return total
