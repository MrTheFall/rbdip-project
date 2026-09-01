from app.db import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    # Denormalized customer data lives directly on the order instead of a
    # customers table with a foreign key.
    customer_full_name = db.Column(db.String(255), nullable=False)
    customer_address = db.Column(db.String(500))
    customer_phone = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default="new")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    items = db.relationship("OrderItem", backref="order", lazy="select")


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    # product_name/product_price are copied at order time instead of
    # referencing products via a foreign key.
    product_name = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    author_name = db.Column(db.String(255))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
