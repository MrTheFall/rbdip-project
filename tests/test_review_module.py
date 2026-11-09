"""ЛР4: после выделения модуля review его API работает как раньше."""


def _create_product(client, name="Clean Code", price="45.00"):
    resp = client.post("/products", json={"name": name, "price": price})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_add_and_list_reviews(client):
    product_id = _create_product(client)

    created = client.post(
        f"/products/{product_id}/reviews",
        json={"author_name": "Ada", "rating": 5, "comment": "Great read"},
    )
    assert created.status_code == 201
    assert created.get_json()["id"]

    listed = client.get(f"/products/{product_id}/reviews")
    assert listed.status_code == 200
    assert listed.get_json() == [
        {"author_name": "Ada", "rating": 5, "comment": "Great read"}
    ]


def test_review_author_defaults_to_anonymous(client):
    product_id = _create_product(client)
    client.post(f"/products/{product_id}/reviews", json={"rating": 4})

    listed = client.get(f"/products/{product_id}/reviews").get_json()
    assert listed[0]["author_name"] == "anonymous"
