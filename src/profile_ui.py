from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal

FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
C_GREEN = "#4ade80"
C_GREEN_D = "#22c55e"

PROFILE_COLORS = [
    ("#4ade80", "Green"),
    ("#60a5fa", "Blue"),
    ("#f472b6", "Pink"),
    ("#fb923c", "Orange"),
    ("#a78bfa", "Purple"),
    ("#facc15", "Yellow"),
    ("#f87171", "Red"),
    ("#94a3b8", "Gray"),
]


class ProfileEditorPanel(QWidget):
    """Embedded panel for creating or editing a profile."""
    closed = pyqtSignal()
    saved = pyqtSignal(dict)

    def __init__(self, parent=None, profile=None, versions=None):
        super().__init__(parent)
        self.profile = profile
        self.result_data = None
        is_edit = profile is not None

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("profileRoot")
        self.setStyleSheet(f"""
            QWidget#profileRoot {{
                background-color: rgba(11, 11, 11, 0.92);
                color: #e8e8e8;
                font-family: {FONT};
            }}
            QWidget#profileRoot QWidget {{
                background: transparent;
                color: #e8e8e8;
                font-family: {FONT};
            }}
            QLabel {{
                color: #ccc;
                font-size: 13px;
                background: transparent;
            }}
            QLineEdit {{
                padding: 10px 14px;
                background-color: rgba(255,255,255,0.05);
                color: white;
                font-size: 13px;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C_GREEN};
            }}
            QComboBox {{
                padding: 10px 14px;
                background-color: rgba(255,255,255,0.05);
                color: white;
                font-size: 13px;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ image: none; }}
            QComboBox QAbstractItemView {{
                background-color: #1c1c1c;
                color: white;
                selection-background-color: #16a34a;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }}
            QPushButton {{
                background-color: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                color: white;
                padding: 10px 18px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.15);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(16)

        # ── Header with back button ──
        header_row = QHBoxLayout()
        back_btn = QPushButton("← Geri")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._on_close)
        header_row.addWidget(back_btn)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Title
        title = QLabel("Edit Profile" if is_edit else "New Profile")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: white;")
        layout.addWidget(title)

        # Field label style
        lbl_ss = "color: rgba(255,255,255,0.45); font-size: 10px; font-weight: 600; letter-spacing: 1.5px;"

        # Name
        lbl_name = QLabel("PROFILE NAME")
        lbl_name.setStyleSheet(lbl_ss)
        layout.addWidget(lbl_name)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("My Profile")
        if is_edit:
            self.name_input.setText(profile["name"])
        layout.addWidget(self.name_input)

        # Version + Loader row
        row = QHBoxLayout()
        row.setSpacing(12)

        v_col = QVBoxLayout()
        v_col.setSpacing(4)
        lbl_ver = QLabel("VERSION")
        lbl_ver.setStyleSheet(lbl_ss)
        v_col.addWidget(lbl_ver)
        self.version_combo = QComboBox()
        if versions:
            self.version_combo.addItems(versions)
        if is_edit and profile.get("version"):
            idx = self.version_combo.findText(profile["version"])
            if idx >= 0:
                self.version_combo.setCurrentIndex(idx)
        v_col.addWidget(self.version_combo)
        row.addLayout(v_col)

        l_col = QVBoxLayout()
        l_col.setSpacing(4)
        lbl_ldr = QLabel("LOADER")
        lbl_ldr.setStyleSheet(lbl_ss)
        l_col.addWidget(lbl_ldr)
        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["Vanilla", "Fabric", "Forge", "Quilt", "NeoForge"])
        if is_edit and profile.get("loader"):
            idx = self.loader_combo.findText(profile["loader"])
            if idx >= 0:
                self.loader_combo.setCurrentIndex(idx)
        l_col.addWidget(self.loader_combo)
        row.addLayout(l_col)

        layout.addLayout(row)

        # Color picker
        lbl_color = QLabel("COLOR")
        lbl_color.setStyleSheet(lbl_ss)
        layout.addWidget(lbl_color)

        color_row = QHBoxLayout()
        color_row.setSpacing(8)
        self.selected_color = profile["color"] if is_edit else PROFILE_COLORS[0][0]
        self.color_buttons = []

        for hex_color, name in PROFILE_COLORS:
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("hex", hex_color)
            btn.clicked.connect(lambda checked, c=hex_color: self._select_color(c))
            self.color_buttons.append(btn)
            color_row.addWidget(btn)
        color_row.addStretch()
        layout.addLayout(color_row)
        self._update_color_buttons()

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self._on_close)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save" if is_edit else "Create")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_GREEN_D};
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                padding: 10px 28px;
            }}
            QPushButton:hover {{
                background-color: {C_GREEN};
            }}
        """)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _on_close(self):
        self.closed.emit()

    def _select_color(self, hex_color):
        self.selected_color = hex_color
        self._update_color_buttons()

    def _update_color_buttons(self):
        for btn in self.color_buttons:
            c = btn.property("hex")
            is_active = c == self.selected_color
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c};
                    border: 3px solid {"white" if is_active else "transparent"};
                    border-radius: 16px;
                }}
                QPushButton:hover {{
                    border: 3px solid rgba(255,255,255,0.5);
                }}
            """)

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setPlaceholderText("⚠ Enter a name!")
            return
        self.result_data = {
            "name": name,
            "version": self.version_combo.currentText(),
            "loader": self.loader_combo.currentText(),
            "color": self.selected_color,
        }
        self.saved.emit(self.result_data)
        self.closed.emit()
