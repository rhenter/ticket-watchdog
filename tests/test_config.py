import yaml

from src.config import load_sla_config, get_sla_config


def test_load_and_get_sla_config(tmp_path, monkeypatch):
    cfg = {
        "tiers": {
            "gold": {"high": {"response": 10, "resolution": 20}}
        }
    }
    config_file = tmp_path / "sla.yaml"
    config_file.write_text(yaml.dump(cfg))
    monkeypatch.setenv("SLA_CONFIG_PATH", str(config_file))

    # Reload
    load_sla_config(str(config_file))
    loaded = get_sla_config()
    assert "gold" in loaded
    assert loaded["gold"]["high"]["response"] == 10


def test_load_sla_config_file_not_found(monkeypatch):
    from src.config import load_sla_config
    # Should not raise, just log error
    load_sla_config("/nonexistent/path.yaml")


def test_load_sla_config_invalid_yaml(tmp_path, monkeypatch):
    from src.config import load_sla_config
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text(": invalid yaml :")
    # Should not raise, just log error
    load_sla_config(str(bad_file))


def test_config_handler_on_modified(monkeypatch, tmp_path):
    from src.config import SLAConfigHandler
    import os
    config_file = tmp_path / "sla.yaml"
    config_file.write_text("tiers: {}\n")
    handler = SLAConfigHandler(str(config_file))
    # Should not raise, just log info
    class DummyEvent:
        def __init__(self, path):
            self.src_path = path
    handler.on_modified(DummyEvent(str(config_file)))
