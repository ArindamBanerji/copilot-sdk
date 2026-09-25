"""Disposable clone isolation: preserve earned live Trading state."""


def test_clone_fingerprint_is_cold_and_does_not_reset_live(client):
    before = client.get("/api/fingerprint").json()
    response = client.get("/api/self/clone-fingerprint")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["instance_kind"] == "disposable_clean_clone"
    assert body["decisions_analyzed"] == 0
    assert len(body["factors"]) == 10
    assert all(factor["weight"] == 0 for factor in body["factors"])
    assert client.get("/api/fingerprint").json() == before
