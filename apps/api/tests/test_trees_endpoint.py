"""End-to-end test of GET /trees/{topic_id}. Serves the static sample
dataset for now (see the TODO in app/routers/trees.py) — this proves the
501 stub is gone, not that the live pipeline is wired end-to-end yet."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_tree_returns_real_data_not_a_501():
    response = client.get("/trees/intro-to-ml")

    assert response.status_code == 200
    body = response.json()
    assert len(body["nodes"]) > 0
    assert len(body["edges"]) > 0
    # DAG tier invariant, checked against the checked-in sample dataset too.
    level_by_id = {node["id"]: node["level"] for node in body["nodes"]}
    for edge in body["edges"]:
        assert level_by_id[edge["to"]] > level_by_id[edge["from"]]
