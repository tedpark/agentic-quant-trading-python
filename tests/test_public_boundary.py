from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_declares_public_private_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "not investment advice" in readme
    assert "Public / Private Boundary" in readme
    assert "broker integration" in readme
    assert "live strategy thresholds" in readme


def test_inventory_keeps_live_trading_private() -> None:
    inventory = (ROOT / "docs" / "inventory.md").read_text(encoding="utf-8")

    assert "Broker integrations" in inventory
    assert "Live order scripts" in inventory
    assert "Exact entry/exit thresholds" in inventory
