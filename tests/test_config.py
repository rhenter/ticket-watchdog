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
