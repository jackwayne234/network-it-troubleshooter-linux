from pathlib import Path


SOURCE = Path("src/network_it_troubleshooter/__main__.py")


def test_start_screen_prioritizes_run_all_tests_without_json_required():
    source = SOURCE.read_text()

    assert 'QPushButton("Run All Tests")' in source
    assert "run_live_all_tests" in source
    assert 'self.result_label = QLabel("Click Run All Tests to check this computer now. JSON reports are optional.")' in source


def test_open_json_report_is_optional_advanced_path():
    source = SOURCE.read_text()

    assert 'QPushButton("Open JSON Report (optional)")' in source
    assert "JSON reports are optional" in source
