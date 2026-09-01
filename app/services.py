from app.db import db
from app.models import Order, OrderItem, Product


def calculate_order_total(items, customer_type="regular", coupon_code=None):
    total = 0
    for item in items:
        line_price = item["price"] * item["quantity"]
        if item["quantity"] > 10:
            line_price = line_price * 0.95
        total += line_price

    if customer_type == "vip":
        total = total * 0.9
    elif customer_type == "wholesale":
        total = total * 0.85

    if coupon_code == "SAVE10":
        total = total - 10
    elif coupon_code == "SAVE20PERCENT":
        total = total * 0.8

    if total < 0:
        total = 0

    if total > 1000:
        total = total * 0.98

    return round(total, 2)


class OrderService:
    """Handles everything related to placing an order: validation,
    pricing, persistence and notifying the customer."""

    def create_order(self, payload):
        if not payload.get("customer_full_name"):
            raise ValueError("customer_full_name is required")
        if not payload.get("customer_address"):
            raise ValueError("customer_address is required")
        if not payload.get("items"):
            raise ValueError("order must contain at least one item")

        line_items = []
        for raw_item in payload["items"]:
            product = Product.query.get(raw_item["product_id"])
            if product is None:
                raise ValueError(f"product {raw_item['product_id']} not found")
            quantity = raw_item.get("quantity", 1)
            if quantity <= 0:
                raise ValueError("quantity must be positive")
            line_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "price": float(product.price),
                }
            )

        total = calculate_order_total(
            [{"price": li["price"], "quantity": li["quantity"]} for li in line_items],
            customer_type=payload.get("customer_type", "regular"),
            coupon_code=payload.get("coupon_code"),
        )

        order = Order(
            customer_full_name=payload["customer_full_name"],
            customer_address=payload["customer_address"],
            customer_phone=payload.get("customer_phone"),
            status="new",
        )
        db.session.add(order)
        db.session.flush()

        for li in line_items:
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_name=li["product"].name,
                    product_price=li["price"],
                    quantity=li["quantity"],
                )
            )

        db.session.commit()

        self._send_confirmation_email(payload["customer_full_name"], order.id, total)

        return order

    def _send_confirmation_email(self, customer_name, order_id, total):
        # No real mail transport is configured for the training project;
        # this stands in for the notification side-effect.
        print(f"[email] Dear {customer_name}, your order #{order_id} "
              f"for {total} has been placed.")
