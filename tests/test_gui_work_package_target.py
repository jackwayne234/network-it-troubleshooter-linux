from pathlib import Path


SOURCE = Path("src/network_it_troubleshooter/__main__.py")


def test_web_https_gui_has_target_field_and_passes_it_to_steps():
    source = SOURCE.read_text()

    assert "website_target_field" in source
    assert "Website to test" in source
    assert "steps_for_flow(self.current_analysis.flow_used, self.website_target())" in source


def test_healthy_gui_shows_website_target_field():
    source = SOURCE.read_text()

    assert "Healthy Flow" in source
    assert "Website to test" in source


def test_unknown_mixed_gui_shows_website_target_field():
    source = SOURCE.read_text()

    assert 'analysis.flow_used in {"Healthy Flow", "Unknown/Mixed Issue Flow", "Web/HTTPS Problem Flow"}' in source
