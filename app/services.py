from app.db import db
from app.models import Customer, Order, OrderItem, Product
from app.pricing import PricingCalculator


def calculate_order_total(items, customer_type="regular", coupon_code=None):
    """Backward-compatible helper kept for callers that price items directly."""
    return PricingCalculator().calculate(items, customer_type, coupon_code)


def split_customer_name(full_name):
    """Splits the single name from the request into first and last name."""
    parts = full_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else None
    return first_name, last_name


class OrderValidator:
    """Checks an order request and turns its items into line items.

    A line item carries the resolved product, the requested quantity and the
    price captured at order time.
    """

    def __init__(self, repository):
        self.repository = repository

    def validate(self, payload):
        if not payload.get("customer_full_name"):
            raise ValueError("customer_full_name is required")
        if not payload.get("customer_address"):
            raise ValueError("customer_address is required")
        if not payload.get("items"):
            raise ValueError("order must contain at least one item")
        return [self._line_item(raw_item) for raw_item in payload["items"]]

    def _line_item(self, raw_item):
        product = self.repository.get_product(raw_item["product_id"])
        if product is None:
            raise ValueError(f"product {raw_item['product_id']} not found")
        quantity = raw_item.get("quantity", 1)
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return {
            "product": product,
            "quantity": quantity,
            "price": float(product.price),
        }


class OrderRepository:
    """Reads the products referenced by an order and stores customers and orders."""

    def get_product(self, product_id):
        return Product.query.get(product_id)

    def get_or_create_customer(self, full_name, address, phone):
        first_name, last_name = split_customer_name(full_name)
        customer = Customer.query.filter_by(
            first_name=first_name, last_name=last_name, address=address, phone=phone
        ).first()
        if customer is None:
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                address=address,
                phone=phone,
            )
            db.session.add(customer)
            db.session.flush()
        return customer

    def save(self, payload, line_items):
        customer = self.get_or_create_customer(
            full_name=payload["customer_full_name"],
            address=payload["customer_address"],
            phone=payload.get("customer_phone"),
        )

        order = Order(customer_id=customer.id, status="new")
        db.session.add(order)
        db.session.flush()

        for line_item in line_items:
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=line_item["product"].id,
                    quantity=line_item["quantity"],
                )
            )

        db.session.commit()
        return order


class OrderNotifier:
    """Notifies the customer that an order has been placed."""

    def send_confirmation(self, customer_name, order_id, total):
        # No real mail transport is configured for the training project;
        # this stands in for the notification side-effect.
        print(f"[email] Dear {customer_name}, your order #{order_id} "
              f"for {total} has been placed.")


class OrderService:
    """Places an order: validates the request, prices it, stores it and
    notifies the customer. Each concern is delegated to a collaborator."""

    def __init__(self):
        self.repository = OrderRepository()
        self.validator = OrderValidator(self.repository)
        self.pricing = PricingCalculator()
        self.notifier = OrderNotifier()

    def create_order(self, payload):
        line_items = self.validator.validate(payload)

        total = self.pricing.calculate(
            line_items,
            customer_type=payload.get("customer_type", "regular"),
            coupon_code=payload.get("coupon_code"),
        )

        order = self.repository.save(payload, line_items)

        self.notifier.send_confirmation(payload["customer_full_name"], order.id, total)

        return order
