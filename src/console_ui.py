"""
Embedded game console panel — runs Minecraft as a subprocess and
streams stdout / stderr into a QTextEdit inside the launcher.
"""
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QFont, QTextCursor, QColor

FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "'Cascadia Code', 'Consolas', 'Courier New', monospace"
C_GREEN = "#4ade80"
C_GREEN_D = "#22c55e"


class GameRunnerThread(QThread):
    """Runs the Minecraft process and emits stdout/stderr line by line."""
    output_signal = pyqtSignal(str)       # each line of output
    error_signal = pyqtSignal(str)        # each line of stderr
    finished_signal = pyqtSignal(int)     # exit code

    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.command = command
        self._process = None

    def run(self):
        try:
            self._process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            # Read stdout in real time
            for line in iter(self._process.stdout.readline, ""):
                if line:
                    self.output_signal.emit(line.rstrip("\n"))

            # After stdout closes, drain stderr
            for line in iter(self._process.stderr.readline, ""):
                if line:
                    self.error_signal.emit(line.rstrip("\n"))

            self._process.wait()
            self.finished_signal.emit(self._process.returncode)
        except Exception as e:
            self.error_signal.emit(f"[QLauncher] Process error: {e}")
            self.finished_signal.emit(-1)

    def kill_process(self):
        if self._process and self._process.poll() is None:
            self._process.kill()


class ConsolePanel(QWidget):
    """Embedded console panel shown inside the launcher while the game runs."""
    closed = pyqtSignal()

    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("consoleRoot")
        self.setStyleSheet(f"""
            QWidget#consoleRoot {{
                background-color: rgba(8, 8, 8, 0.95);
                color: #e8e8e8;
                font-family: {FONT};
            }}
            QWidget#consoleRoot QWidget {{
                background: transparent;
                color: #e8e8e8;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("🎮  Game Console")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: white;")
        header.addWidget(title)

        self.status_label = QLabel("● Running")
        self.status_label.setStyleSheet(f"color: {C_GREEN}; font-weight: 600; font-size: 13px;")
        header.addWidget(self.status_label)
        header.addStretch()

        self.kill_btn = QPushButton("⬛ Kill")
        self.kill_btn.setCursor(Qt.PointingHandCursor)
        self.kill_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 8px;
                color: #ef4444;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid rgba(239, 68, 68, 0.5);
            }
        """)
        self.kill_btn.clicked.connect(self._kill_game)
        header.addWidget(self.kill_btn)

        self.close_btn = QPushButton("← Geri")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                color: white;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.15);
            }
        """)
        self.close_btn.clicked.connect(lambda: self.closed.emit())
        self.close_btn.setEnabled(False)
        header.addWidget(self.close_btn)

        layout.addLayout(header)

        # ── Console output ──
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Cascadia Code, Consolas, Courier New", 10))
        self.console.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(0, 0, 0, 0.6);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 10px;
                padding: 12px;
                color: #ccc;
                font-size: 12px;
                selection-background-color: rgba(74, 222, 128, 0.2);
            }}
        """)
        layout.addWidget(self.console)

        # ── Start the game thread ──
        self.runner = GameRunnerThread(command)
        self.runner.output_signal.connect(self._on_stdout)
        self.runner.error_signal.connect(self._on_stderr)
        self.runner.finished_signal.connect(self._on_finished)
        self.runner.start()

        self._append_system(f"[QLauncher] Game process started...")

    def _append_system(self, text):
        self.console.setTextColor(QColor(74, 222, 128))
        self.console.append(text)
        self.console.moveCursor(QTextCursor.End)

    def _on_stdout(self, line):
        self.console.setTextColor(QColor(200, 200, 200))
        self.console.append(line)
        self.console.moveCursor(QTextCursor.End)

    def _on_stderr(self, line):
        self.console.setTextColor(QColor(248, 113, 113))
        self.console.append(line)
        self.console.moveCursor(QTextCursor.End)

    def _on_finished(self, exit_code):
        if exit_code == 0:
            self._append_system(f"[QLauncher] Game exited successfully (code {exit_code}).")
            self.status_label.setText("● Finished")
            self.status_label.setStyleSheet("color: #60a5fa; font-weight: 600; font-size: 13px;")
        else:
            self._append_system(f"[QLauncher] Game exited with code {exit_code}.")
            self.status_label.setText("● Crashed")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: 600; font-size: 13px;")

        self.kill_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

    def _kill_game(self):
        self.runner.kill_process()
        self._append_system("[QLauncher] Game process killed by user.")
