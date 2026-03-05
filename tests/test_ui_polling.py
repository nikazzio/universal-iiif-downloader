from studio_ui.common import polling


def test_download_polling_intervals_use_config_values(monkeypatch):
    """Polling helpers should read configured values from settings."""

    def _fake_get_setting(path, default=None):
        if path == "ui.polling.download_manager_interval_seconds":
            return 7
        if path == "ui.polling.download_status_interval_seconds":
            return 5
        return default

    monkeypatch.setattr(polling, "get_setting", _fake_get_setting)

    assert polling.get_download_manager_interval_seconds() == 7
    assert polling.get_download_status_interval_seconds() == 5
    assert polling.build_every_seconds_trigger(7) == "every 7s"


def test_download_polling_intervals_clamp_invalid_values(monkeypatch):
    """Out-of-range or invalid values should stay inside the supported bounds."""

    def _fake_get_setting(path, default=None):
        if path == "ui.polling.download_manager_interval_seconds":
            return "nope"
        if path == "ui.polling.download_status_interval_seconds":
            return 99
        return default

    monkeypatch.setattr(polling, "get_setting", _fake_get_setting)

    assert polling.get_download_manager_interval_seconds() == 3
    assert polling.get_download_status_interval_seconds() == 30
    assert polling.build_every_seconds_trigger(0) == "every 1s"
