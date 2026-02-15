
import sys
import os
import random
import requests
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QComboBox, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QProgressBar,
    QMessageBox, QGraphicsDropShadowEffect, QFrame, QStackedWidget
)
from PyQt5.QtGui import (
    QPixmap, QPalette, QBrush, QImage, QColor, QFont,
    QPainter, QIcon, QLinearGradient
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from .backend import LauncherBackend
from .profile_manager import ProfileManager


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Design Tokens
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
C_BG       = "#0f0f0f"
C_PANEL    = "rgba(18, 18, 22, 0.92)"
C_SURFACE  = "rgba(255, 255, 255, 0.06)"
C_BORDER   = "rgba(255, 255, 255, 0.08)"
C_TEXT     = "#f0f0f0"
C_TEXT_DIM = "rgba(255, 255, 255, 0.45)"
C_GREEN    = "#4ade80"
C_GREEN_D  = "#22c55e"
C_GREEN_DD = "#16a34a"
C_INPUT_BG = "rgba(255, 255, 255, 0.05)"
C_INPUT_BD = "rgba(255, 255, 255, 0.10)"
C_HOVER    = "rgba(255, 255, 255, 0.08)"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Version Fetcher Thread
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class VersionFetcherThread(QThread):
    versions_signal = pyqtSignal(list)

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

    def run(self):
        try:
            versions = self.backend.get_vanilla_versions()
            self.versions_signal.emit(versions)
        except Exception as e:
            print(f"Error fetching versions: {e}")
            self.versions_signal.emit([])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main Window
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QLauncher")
        self.setFixedSize(1333, 700)

        self.minecraft_dir = os.path.join(os.getenv('APPDATA'), '.minecraft')
        self.backend = LauncherBackend(self.minecraft_dir)
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
        self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Profile Manager
        self.profile_manager = ProfileManager(self.app_dir)
        self.available_versions = []

        icon_path = os.path.join(self.assets_dir, 'app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.initUI()

    def initUI(self):
        # ── Stacked widget: page 0 = main, overlay panels added dynamically ──
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_page = QWidget()
        self.stack.addWidget(self.main_page)
        self.setup_background()

        main_layout = QVBoxLayout(self.main_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Top Bar ───
        top_bar = QWidget()
        top_bar.setFixedHeight(90)
        top_bar.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(40, 25, 40, 0)
        top_layout.setSpacing(12)

        title_label = QLabel("QLauncher")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 28px;
                font-weight: 700;
                font-family: {FONT};
                background: transparent;
                border: none;
                letter-spacing: 1px;
            }}
        """)
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setColor(QColor(74, 222, 128, 120))
        glow.setOffset(0, 0)
        title_label.setGraphicsEffect(glow)
        top_layout.addWidget(title_label)

        ver_badge = QLabel("v2.0")
        ver_badge.setFixedSize(42, 22)
        ver_badge.setAlignment(Qt.AlignCenter)
        ver_badge.setStyleSheet(f"""
            QLabel {{
                color: {C_GREEN};
                font-size: 10px;
                font-weight: bold;
                font-family: {FONT};
                background: rgba(74, 222, 128, 0.12);
                border: 1px solid rgba(74, 222, 128, 0.25);
                border-radius: 11px;
            }}
        """)
        top_layout.addWidget(ver_badge, 0, Qt.AlignVCenter)
        top_layout.addStretch()

        main_layout.addWidget(top_bar)
        main_layout.addStretch()

        # ─── Bottom Control Panel (Glass) ───
        controls_panel = QWidget()
        controls_panel.setObjectName("ctrls")
        controls_panel.setFixedHeight(110)
        controls_panel.setStyleSheet(f"""
            QWidget#ctrls {{
                background-color: {C_PANEL};
                border-top: 1px solid {C_BORDER};
            }}
        """)

        controls_layout = QHBoxLayout(controls_panel)
        controls_layout.setContentsMargins(40, 0, 40, 0)
        controls_layout.setSpacing(18)

        # ── Shared Styles ──
        input_ss = f"""
            QLineEdit {{
                padding: 10px 14px;
                font-size: 13px;
                font-family: {FONT};
                background-color: {C_INPUT_BG};
                color: {C_TEXT};
                border: 1px solid {C_INPUT_BD};
                border-radius: 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C_GREEN};
                background-color: rgba(74, 222, 128, 0.04);
            }}
        """
        combo_ss = f"""
            QComboBox {{
                padding: 10px 14px;
                font-size: 13px;
                font-family: {FONT};
                background-color: {C_INPUT_BG};
                color: {C_TEXT};
                border: 1px solid {C_INPUT_BD};
                border-radius: 8px;
            }}
            QComboBox:hover {{
                border: 1px solid rgba(255,255,255,0.18);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: #1c1c1c;
                color: white;
                selection-background-color: {C_GREEN_DD};
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }}
        """
        label_ss = f"color: {C_TEXT_DIM}; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; background: transparent; border: none; font-family: {FONT};"

        # Username
        u_widget = QWidget()
        u_layout = QVBoxLayout(u_widget)
        u_layout.setContentsMargins(0, 0, 0, 0)
        u_layout.setSpacing(6)
        u_lbl = QLabel("USERNAME")
        u_lbl.setStyleSheet(label_ss)
        u_layout.addWidget(u_lbl)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Steve")
        self.username_input.setFixedWidth(190)
        self.username_input.setStyleSheet(input_ss)
        u_layout.addWidget(self.username_input)
        controls_layout.addWidget(u_widget, 0, Qt.AlignVCenter)

        # Version
        v_widget = QWidget()
        v_layout = QVBoxLayout(v_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(6)
        v_lbl = QLabel("VERSION")
        v_lbl.setStyleSheet(label_ss)
        v_layout.addWidget(v_lbl)
        self.version_combo = QComboBox()
        self.version_combo.setFixedWidth(155)
        self.version_combo.addItem("Loading...")
        self.version_combo.setStyleSheet(combo_ss)
        self.populate_versions()
        v_layout.addWidget(self.version_combo)
        controls_layout.addWidget(v_widget, 0, Qt.AlignVCenter)

        # Loader
        l_widget = QWidget()
        l_layout = QVBoxLayout(l_widget)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(6)
        l_lbl = QLabel("LOADER")
        l_lbl.setStyleSheet(label_ss)
        l_layout.addWidget(l_lbl)
        self.modloader_combo = QComboBox()
        self.modloader_combo.addItems(["Vanilla", "Fabric", "Forge", "Quilt", "NeoForge"])
        self.modloader_combo.setFixedWidth(130)
        self.modloader_combo.setStyleSheet(combo_ss)
        l_layout.addWidget(self.modloader_combo)
        controls_layout.addWidget(l_widget, 0, Qt.AlignVCenter)

        # ── Separator ──
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(50)
        sep.setStyleSheet(f"background-color: {C_BORDER};")
        controls_layout.addWidget(sep, 0, Qt.AlignVCenter)

        # ── Profile Selector ──
        p_widget = QWidget()
        p_widget.setMinimumWidth(280)
        p_layout = QVBoxLayout(p_widget)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(6)
        p_lbl = QLabel("PROFILE")
        p_lbl.setStyleSheet(label_ss)
        p_layout.addWidget(p_lbl)

        p_row = QHBoxLayout()
        p_row.setSpacing(4)
        self.profile_combo = QComboBox()
        self.profile_combo.setFixedWidth(140)
        self.profile_combo.setStyleSheet(combo_ss)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        p_row.addWidget(self.profile_combo)

        # + button (new profile)
        add_btn = QPushButton("+")
        add_btn.setFixedSize(36, 36)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
                color: {C_GREEN};
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C_HOVER};
                border: 1px solid rgba(255,255,255,0.15);
            }}
        """)
        add_btn.clicked.connect(self._new_profile)
        p_row.addWidget(add_btn)

        # edit button
        edit_btn = QPushButton("✎")
        edit_btn.setFixedSize(36, 36)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
                color: {C_TEXT_DIM};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {C_HOVER};
                color: white;
                border: 1px solid rgba(255,255,255,0.15);
            }}
        """)
        edit_btn.clicked.connect(self._edit_profile)
        p_row.addWidget(edit_btn)

        # delete button
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(36, 36)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
                color: {C_TEXT_DIM};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(239, 68, 68, 0.15);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }}
        """)
        del_btn.clicked.connect(self._delete_profile)
        p_row.addWidget(del_btn)

        p_layout.addLayout(p_row)
        controls_layout.addWidget(p_widget, 0, Qt.AlignVCenter)

        controls_layout.addStretch()

        # ── Action Buttons ──
        btn_base = f"""
            QPushButton {{
                font-family: {FONT};
                font-weight: 600;
                border-radius: 8px;
                padding: 0;
            }}
        """

        # Settings
        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(44, 44)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: {C_SURFACE};
                border: 1px solid {C_BORDER};
                color: {C_TEXT_DIM};
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {C_HOVER};
                color: white;
                border: 1px solid rgba(255,255,255,0.15);
            }}
        """)
        self.settings_button.clicked.connect(self.open_settings)
        controls_layout.addWidget(self.settings_button, 0, Qt.AlignVCenter)

        # Mods
        self.mods_button = QPushButton("MODS")
        self.mods_button.setFixedSize(100, 44)
        self.mods_button.setCursor(Qt.PointingHandCursor)
        self.mods_button.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: {C_SURFACE};
                border: 1px solid {C_BORDER};
                color: {C_TEXT};
                font-size: 13px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {C_HOVER};
                border: 1px solid rgba(255,255,255,0.15);
            }}
        """)
        self.mods_button.clicked.connect(self.open_mod_manager)
        controls_layout.addWidget(self.mods_button, 0, Qt.AlignVCenter)

        # Play
        self.play_button = QPushButton("▶   P L A Y")
        self.play_button.setFixedSize(200, 50)
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: {C_GREEN_D};
                border: none;
                color: white;
                font-size: 15px;
                letter-spacing: 3px;
            }}
            QPushButton:hover {{
                background-color: {C_GREEN};
            }}
            QPushButton:pressed {{
                background-color: {C_GREEN_DD};
            }}
            QPushButton:disabled {{
                background-color: rgba(34, 197, 94, 0.3);
                color: rgba(255,255,255,0.5);
            }}
        """)
        play_glow = QGraphicsDropShadowEffect()
        play_glow.setBlurRadius(25)
        play_glow.setColor(QColor(34, 197, 94, 90))
        play_glow.setOffset(0, 2)
        self.play_button.setGraphicsEffect(play_glow)
        self.play_button.clicked.connect(self.launch_game)
        controls_layout.addWidget(self.play_button, 0, Qt.AlignVCenter)

        main_layout.addWidget(controls_panel)

        # ─── Progress Bar ───
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {C_BG};
            }}
            QProgressBar::chunk {{
                background-color: {C_GREEN};
            }}
        """)
        main_layout.addWidget(self.progress_bar)

        self.load_settings()

    # ─── Background ───
    def setup_background(self):
        import requests
        bg_path = os.path.join(self.assets_dir, 'background.jpeg')

        if not os.path.exists(bg_path):
             try:
                 url = "https://images.wallpapersden.com/image/download/minecraft-shaders-hd-nature_bGdtaWyUmZqaraWkpJRmbmdlrWZlbWU.jpg"
                 r = requests.get(url, stream=True)
                 if r.status_code == 200:
                     if not os.path.exists(self.assets_dir):
                         os.makedirs(self.assets_dir)
                     with open(bg_path, 'wb') as f:
                         for chunk in r.iter_content(1024):
                             f.write(chunk)
             except Exception as e:
                 print(f"Failed to download background: {e}")

        if os.path.exists(bg_path):
            self.background_pixmap = QPixmap(bg_path)
        else:
            self.background_pixmap = None

    def paintEvent(self, event):
        painter = QPainter(self)
        if hasattr(self, 'background_pixmap') and self.background_pixmap:
            cw = self.width()
            ch = self.height()
            iw = self.background_pixmap.width()
            ih = self.background_pixmap.height()
            if iw == 0 or ih == 0: return

            scale = max(cw / iw, ch / ih)
            new_w = int(iw * scale)
            new_h = int(ih * scale)
            x = (cw - new_w) // 2
            y = (ch - new_h) // 2

            scaled = self.background_pixmap.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(x, y, scaled)

            # Vignette / darken overlay
            painter.fillRect(0, 0, cw, ch, QColor(0, 0, 0, 80))

            # Bottom gradient fade into panel
            grad = QLinearGradient(0, ch - 200, 0, ch)
            grad.setColorAt(0.0, QColor(0, 0, 0, 0))
            grad.setColorAt(1.0, QColor(15, 15, 15, 230))
            painter.fillRect(0, ch - 200, cw, 200, grad)
        else:
            painter.fillRect(self.rect(), QColor(15, 15, 15))

    # ─── Versions ───
    def populate_versions(self):
        self.version_loader = VersionFetcherThread(self.backend)
        self.version_loader.versions_signal.connect(self.on_versions_loaded)
        self.version_loader.start()

    def on_versions_loaded(self, versions):
        self.available_versions = versions[:50] if versions else []
        self.version_combo.clear()
        if versions:
             self.version_combo.addItems(self.available_versions)
             self._refresh_profiles()
             self.load_settings()
        else:
             self.version_combo.addItem("No versions found (Network Error?)")

    # ─── Profiles ───
    def _refresh_profiles(self):
        """Populate the profile combo from ProfileManager."""
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        profiles = self.profile_manager.get_profiles()
        active = self.profile_manager.get_active_profile()
        active_idx = 0
        for i, p in enumerate(profiles):
            self.profile_combo.addItem(f"● {p['name']}", p["id"])
            # Color the dot
            if active and p["id"] == active["id"]:
                active_idx = i
        self.profile_combo.setCurrentIndex(active_idx)
        self.profile_combo.blockSignals(False)
        self._apply_profile(active)

    def _on_profile_changed(self, index):
        """Handle profile combo selection change."""
        if index < 0:
            return
        profile_id = self.profile_combo.itemData(index)
        if profile_id:
            self.profile_manager.set_active_profile(profile_id)
            profile = self.profile_manager.get_active_profile()
            self._apply_profile(profile)

    def _apply_profile(self, profile):
        """Apply a profile's settings to the UI combos."""
        if not profile:
            return
        # Set version
        idx = self.version_combo.findText(profile.get("version", ""))
        if idx >= 0:
            self.version_combo.setCurrentIndex(idx)
        # Set loader
        idx = self.modloader_combo.findText(profile.get("loader", ""))
        if idx >= 0:
            self.modloader_combo.setCurrentIndex(idx)

    def _new_profile(self):
        """Open embedded panel to create a new profile."""
        from .profile_ui import ProfileEditorPanel
        panel = ProfileEditorPanel(self, versions=self.available_versions)
        def on_saved(data):
            p = self.profile_manager.create_profile(data["name"], data["version"], data["loader"], data["color"])
            self.profile_manager.set_active_profile(p["id"])
            self._refresh_profiles()
        panel.saved.connect(on_saved)
        self._show_panel(panel)

    def _edit_profile(self):
        """Open embedded panel to edit the current profile."""
        from .profile_ui import ProfileEditorPanel
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        panel = ProfileEditorPanel(self, profile=profile, versions=self.available_versions)
        def on_saved(data):
            self.profile_manager.update_profile(profile["id"], **data)
            self._refresh_profiles()
        panel.saved.connect(on_saved)
        self._show_panel(panel)

    def _delete_profile(self):
        """Delete the current profile after confirmation."""
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        if len(self.profile_manager.get_profiles()) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "You must have at least one profile.")
            return
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Are you sure you want to delete \"{profile['name']}\"?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.profile_manager.delete_profile(profile["id"])
            self._refresh_profiles()

    # ─── Panel Helpers ───
    def _show_panel(self, panel):
        """Show a QWidget as an overlay panel in the stacked widget."""
        self.stack.addWidget(panel)
        self.stack.setCurrentWidget(panel)
        panel.closed.connect(lambda: self._close_panel(panel))

    def _close_panel(self, panel):
        """Remove overlay panel and return to main view."""
        self.stack.setCurrentWidget(self.main_page)
        self.stack.removeWidget(panel)
        panel.deleteLater()

    # ─── Panels ───
    def open_mod_manager(self):
        from .mod_ui import ModManagerPanel
        version = self.version_combo.currentText()
        loader = self.modloader_combo.currentText()
        profile = self.profile_manager.get_active_profile()
        mods_dir = self.profile_manager.get_mods_dir(profile["id"]) if profile else self.minecraft_dir
        panel = ModManagerPanel(mods_dir, self, current_version=version, current_loader=loader)
        self._show_panel(panel)

    def open_settings(self):
        from .settings_ui import SettingsPanel
        panel = SettingsPanel(self)
        self._show_panel(panel)

    # ─── Launch ───
    def launch_game(self):
        username = self.username_input.text()
        if not username:
            self.username_input.setPlaceholderText("⚠ Enter a username!")
            return

        version = self.version_combo.currentText()
        modloader = self.modloader_combo.currentText()

        self.play_button.setEnabled(False)
        self.mods_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        try:
             def update_progress(text, value):
                 self.progress_bar.setFormat(text)
                 self.progress_bar.setValue(int(value) if value else 0)
                 QApplication.processEvents()

             self.save_settings()
             # Save profile version/loader
             profile = self.profile_manager.get_active_profile()
             if profile:
                 self.profile_manager.update_profile(profile["id"], version=version, loader=modloader)

             # Get the launch command from backend (no longer runs subprocess directly)
             # Use profile-specific game directory
             game_dir = None
             if profile:
                 game_dir = self.profile_manager.get_game_dir(profile["id"])
             minecraft_command = self.backend.launch_game(version, modloader, username, progress_callback=update_progress, game_dir=game_dir)

             self.progress_bar.setVisible(False)
             self.play_button.setEnabled(True)
             self.mods_button.setEnabled(True)

             # Open embedded console panel
             if minecraft_command:
                 from .console_ui import ConsolePanel
                 console = ConsolePanel(minecraft_command, self)
                 self._show_panel(console)

        except Exception as e:
             QMessageBox.critical(self, "Launch Error", str(e))
             self.progress_bar.setVisible(False)
             self.play_button.setEnabled(True)
             self.mods_button.setEnabled(True)

    # ─── Settings Persistence ───
    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)

                username = settings.get("username", "")
                if username:
                    self.username_input.setText(username)

                version = settings.get("version", "")
                if version:
                    index = self.version_combo.findText(version)
                    if index >= 0:
                        self.version_combo.setCurrentIndex(index)

                loader = settings.get("loader", "")
                if loader:
                    index = self.modloader_combo.findText(loader)
                    if index >= 0:
                        self.modloader_combo.setCurrentIndex(index)

        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save all settings — merges existing settings.json with current UI state."""
        try:
            settings = {}
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)

            # Main window values
            settings["username"] = self.username_input.text()
            settings["version"] = self.version_combo.currentText()
            settings["loader"] = self.modloader_combo.currentText()

            # Active profile
            profile = self.profile_manager.get_active_profile()
            if profile:
                settings["active_profile"] = profile["id"]

            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

