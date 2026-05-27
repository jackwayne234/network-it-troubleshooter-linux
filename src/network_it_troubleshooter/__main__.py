from __future__ import annotations

import html
import json
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .engine import TroubleshootingAnalysis, analyze_report
from .report_loader import load_report
from .work_package import WorkPackageResult, WorkPackageStep, live_all_tests_steps, run_step, steps_for_flow, summarize_work_package, upsert_work_result


class WorkSignals(QObject):
    finished = Signal(list)


class WorkPackageWorker(QRunnable):
    def __init__(self, steps: list[WorkPackageStep]) -> None:
        super().__init__()
        self.steps = steps
        self.signals = WorkSignals()

    @Slot()
    def run(self) -> None:
        self.signals.finished.emit([run_step(step) for step in self.steps])


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Network IT Troubleshooter")
        self.resize(900, 760)
        self.thread_pool = QThreadPool.globalInstance()
        self.active_workers: list[WorkPackageWorker] = []
        self.current_analysis: TroubleshootingAnalysis | None = None
        self.current_report: dict | None = None
        self.work_results: list[WorkPackageResult] = []
        self.work_running = False
        self.details_visible = False
        self.website_target_field = QLineEdit()
        self.website_target_field.setPlaceholderText("example.com")
        self.website_target_field.setText("example.com")

        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("<h1>Network IT Troubleshooter</h1>")
        subtitle = QLabel("Click Run All Tests to check this computer now. JSON reports are optional and are only needed when you want to analyze a saved report.")
        subtitle.setWordWrap(True)

        button_row = QHBoxLayout()
        run_all_live_button = QPushButton("Run All Tests")
        run_all_live_button.clicked.connect(self.run_live_all_tests)
        open_button = QPushButton("Open JSON Report (optional)")
        open_button.clicked.connect(self.open_report)
        copy_button = QPushButton("Copy IT Summary")
        copy_button.clicked.connect(self.copy_it_summary)
        self.details_button = QPushButton("Show report details")
        self.details_button.clicked.connect(self.toggle_details)
        button_row.addWidget(run_all_live_button)
        button_row.addWidget(open_button)
        button_row.addWidget(copy_button)
        button_row.addWidget(self.details_button)
        button_row.addStretch()

        self.result_label = QLabel("Click Run All Tests to check this computer now. JSON reports are optional.")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-size: 15px;")

        self.work_package_widget = QWidget()
        self.work_package_layout = QVBoxLayout(self.work_package_widget)
        self.work_package_widget.hide()
        self.work_output = QTextEdit()
        self.work_output.setReadOnly(True)
        self.work_summary_label = QLabel("")
        self.work_summary_label.setWordWrap(True)

        self.details_box = QTextEdit()
        self.details_box.setReadOnly(True)
        self.details_box.hide()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(button_row)
        layout.addWidget(self.result_label)
        layout.addWidget(self.work_package_widget)
        layout.addWidget(self.details_box)
        self.setCentralWidget(page)

    def run_live_all_tests(self) -> None:
        self.current_report = None
        self.current_analysis = TroubleshootingAnalysis(
            likely_problem="Live network tests",
            flow_used="Unknown/Mixed Issue Flow",
            why="This runs a broad set of safe read-only checks on this computer right now, without requiring a JSON report first.",
            next_step="Review the Work Package Summary after the checks finish. Failed or warning checks point to what to focus on next.",
            it_summary=(
                "Likely problem: Live network tests\n"
                "Flow used: Unknown/Mixed Issue Flow\n"
                "Why: Broad safe read-only checks were run directly on this computer without a JSON report.\n"
                "Next step: Review failed or warning checks in the Work Package results."
            ),
            flow_steps=[],
        )
        self.show_analysis(self.current_analysis)
        self.show_work_package(self.current_analysis)
        self.details_box.setPlainText("No JSON report was loaded. Run All Tests uses live read-only checks on this computer.")
        self.start_work_worker(live_all_tests_steps(self.website_target()))

    def open_report(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open JSON Report", str(Path.home()), "JSON Reports (*.json)")
        if not path:
            return
        try:
            self.current_report = load_report(path)
            self.current_analysis = analyze_report(self.current_report)
            self.show_analysis(self.current_analysis)
            self.show_work_package(self.current_analysis)
            self.details_box.setPlainText(json.dumps(self.current_report, indent=2, sort_keys=True))
        except Exception as exc:
            QMessageBox.warning(self, "Could not open report", str(exc))

    def show_analysis(self, analysis: TroubleshootingAnalysis) -> None:
        flow_html = ""
        if analysis.flow_steps:
            steps = "".join(f"<li>{html.escape(step)}</li>" for step in analysis.flow_steps)
            flow_html = f"<h3>Troubleshooting flow</h3><ol>{steps}</ol>"
        self.result_label.setText(
            "<h2>Result</h2>"
            f"<p><b>Likely problem:</b> {html.escape(analysis.likely_problem)}</p>"
            f"<p><b>Flow used:</b> {html.escape(analysis.flow_used)}</p>"
            f"<p><b>Why:</b> {html.escape(analysis.why)}</p>"
            f"<p><b>Next step:</b> {html.escape(analysis.next_step)}</p>"
            f"{flow_html}"
        )

    def show_work_package(self, analysis: TroubleshootingAnalysis) -> None:
        self._clear_layout(self.work_package_layout)
        self.work_output.clear()
        self.work_results = []
        steps = self.current_work_steps()
        if not steps:
            self.work_package_widget.hide()
            return

        self.work_package_widget.show()
        self.work_package_layout.addWidget(QLabel("<h2>Work Package</h2>"))
        help_text = QLabel("Press a button to run each safe, read-only troubleshooting step. No settings are changed.")
        help_text.setWordWrap(True)
        self.work_package_layout.addWidget(help_text)

        if analysis.flow_used in {"Healthy Flow", "Unknown/Mixed Issue Flow", "Web/HTTPS Problem Flow"}:
            target_row = QHBoxLayout()
            target_row.addWidget(QLabel("Website to test:"))
            target_row.addWidget(self.website_target_field)
            self.work_package_layout.addLayout(target_row)

        action_row = QHBoxLayout()
        run_all_button = QPushButton("Run All Steps")
        run_all_button.clicked.connect(self.run_all_work_steps)
        copy_results_button = QPushButton("Copy Work Package Results")
        copy_results_button.clicked.connect(self.copy_work_package_results)
        clear_button = QPushButton("Clear Work Package Results")
        clear_button.clicked.connect(self.clear_work_results)
        action_row.addWidget(run_all_button)
        action_row.addWidget(copy_results_button)
        action_row.addWidget(clear_button)
        action_row.addStretch()
        self.work_package_layout.addLayout(action_row)

        for step in steps:
            button = QPushButton(step.label)
            button.clicked.connect(lambda _checked=False, label=step.label: self.run_work_step_by_label(label))
            self.work_package_layout.addWidget(button)
        self.work_summary_label.setText("<b>Work Package Summary:</b> No Work Package checks have been run yet.")
        self.work_package_layout.addWidget(self.work_summary_label)
        self.work_package_layout.addWidget(self.work_output)

    def website_target(self) -> str:
        return self.website_target_field.text().strip()

    def current_work_steps(self) -> list[WorkPackageStep]:
        if not self.current_analysis:
            return []
        return steps_for_flow(self.current_analysis.flow_used, self.website_target())

    def run_work_step(self, step: WorkPackageStep) -> None:
        self.start_work_worker([step])

    def run_work_step_by_label(self, label: str) -> None:
        for step in self.current_work_steps():
            if step.label == label:
                self.run_work_step(step)
                return

    def run_all_work_steps(self) -> None:
        if not self.current_analysis:
            return
        self.start_work_worker(steps_for_flow(self.current_analysis.flow_used, self.website_target()))

    def start_work_worker(self, steps: list[WorkPackageStep]) -> None:
        if not steps:
            return
        if self.work_running:
            self.work_summary_label.setText("<b>Work Package Summary:</b> Checks are already running. Please wait.")
            return
        self.work_running = True
        self.set_work_buttons_enabled(False)
        self.work_summary_label.setText("<b>Work Package Summary:</b> Running checks...")
        worker = WorkPackageWorker(steps)
        worker.signals.finished.connect(lambda results, w=worker: self.finish_work_worker(w, results))
        self.active_workers.append(worker)
        self.thread_pool.start(worker)

    def finish_work_worker(self, worker: WorkPackageWorker, results: list[WorkPackageResult]) -> None:
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        self.work_running = False
        self.set_work_buttons_enabled(True)
        for result in results:
            self.work_results = upsert_work_result(self.work_results, result)
        self.render_work_results()
        self.update_work_summary()

    def clear_work_results(self) -> None:
        if self.work_running:
            self.work_summary_label.setText("<b>Work Package Summary:</b> Checks are running. Please wait before clearing.")
            return
        self.work_results = []
        self.work_output.clear()
        self.update_work_summary()

    def set_work_buttons_enabled(self, enabled: bool) -> None:
        for button in self.work_package_widget.findChildren(QPushButton):
            button.setEnabled(enabled)

    def render_work_results(self) -> None:
        self.work_output.clear()
        for result in self.work_results:
            self.work_output.append(self.format_work_result(result))

    def format_work_result(self, result: WorkPackageResult) -> str:
        return (
            f"{result.label}\n"
            f"Status: {result.status}\n"
            f"Summary: {result.summary}\n"
            f"Output:\n{result.output or '(empty)'}\n"
            "\n---\n"
        )

    def update_work_summary(self) -> None:
        if not self.current_analysis:
            return
        summary = summarize_work_package(self.current_analysis.flow_used, self.work_results)
        self.work_summary_label.setText(f"<pre>{html.escape(summary)}</pre>")

    def copy_work_package_results(self) -> None:
        if not self.current_analysis:
            QMessageBox.information(self, "Nothing to copy", "Open a report first.")
            return
        if not self.work_results:
            QMessageBox.information(self, "Nothing to copy", "Run at least one Work Package check first.")
            return
        summary = summarize_work_package(self.current_analysis.flow_used, self.work_results)
        body = "\n".join(self.format_work_result(result) for result in self.work_results)
        QApplication.clipboard().setText(f"{summary}\n\n{body}")
        QMessageBox.information(self, "Copied", "Work Package results copied to clipboard.")

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def copy_it_summary(self) -> None:
        if not self.current_analysis:
            QMessageBox.information(self, "Nothing to copy", "Open a report first.")
            return
        QApplication.clipboard().setText(self.current_analysis.it_summary)
        QMessageBox.information(self, "Copied", "IT summary copied to clipboard.")

    def toggle_details(self) -> None:
        self.details_visible = not self.details_visible
        self.details_box.setVisible(self.details_visible)
        self.details_button.setText("Hide report details" if self.details_visible else "Show report details")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
