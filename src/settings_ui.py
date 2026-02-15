from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QHBoxLayout, 
    QSpinBox, QLineEdit, QCheckBox, QFileDialog, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import json
import os

FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
C_GREEN = "#4ade80"
C_GREEN_D = "#22c55e"
C_GREEN_DD = "#16a34a"

class SettingsPanel(QWidget):
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("settingsRoot")
        self.setStyleSheet(f"""
            QWidget#settingsRoot {{
                background-color: rgba(11, 11, 11, 0.92);
                color: #e8e8e8;
                font-family: {FONT};
            }}
            QWidget#settingsRoot QWidget {{
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
                background-color: rgba(74, 222, 128, 0.04);
            }}
            QSpinBox {{
                padding: 8px 10px;
                background-color: rgba(255,255,255,0.05);
                color: white;
                font-size: 13px;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: transparent;
                border: none;
                width: 16px;
            }}
            QSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid rgba(255,255,255,0.4);
                width: 0; height: 0;
            }}
            QSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid rgba(255,255,255,0.4);
                width: 0; height: 0;
            }}
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: rgba(255,255,255,0.08);
                border-radius: 3px;
                margin: 2px 0;
            }}
            QSlider::handle:horizontal {{
                background: {C_GREEN_D};
                border: 2px solid {C_GREEN};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, x2:1,
                    stop:0 {C_GREEN_DD}, stop:1 {C_GREEN});
                border-radius: 3px;
            }}
            QGroupBox {{
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                margin-top: 16px;
                font-weight: 600;
                color: #ddd;
                padding: 16px 12px 12px 12px;
                background-color: rgba(255,255,255,0.03);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: {C_GREEN};
                font-size: 12px;
                letter-spacing: 0.5px;
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
            QCheckBox {{
                color: rgba(255,255,255,0.7);
                spacing: 8px;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                background-color: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 4px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {C_GREEN_D};
                border-color: {C_GREEN};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(6)

        # ── Header with back button ──
        header_row = QHBoxLayout()
        back_btn = QPushButton("← Geri")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._on_close)
        header_row.addWidget(back_btn)
        header_row.addStretch()
        layout.addLayout(header_row)

        # ── Title ──
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: white; margin-bottom: 4px;")
        layout.addWidget(title)

        # --- Java Settings ---
        java_group = QGroupBox("Java")
        java_layout = QVBoxLayout()
        java_layout.setSpacing(8)
        
        lbl_java = QLabel("Java Executable Path")
        lbl_java.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        java_layout.addWidget(lbl_java)
        
        java_path_layout = QHBoxLayout()
        java_path_layout.setSpacing(8)
        self.java_path_input = QLineEdit()
        self.java_path_input.setPlaceholderText("Auto-detect (leave empty)")
        java_path_layout.addWidget(self.java_path_input)
        
        self.browse_java_button = QPushButton("Browse")
        self.browse_java_button.setCursor(Qt.PointingHandCursor)
        self.browse_java_button.clicked.connect(self.browse_java)
        java_path_layout.addWidget(self.browse_java_button)
        java_layout.addLayout(java_path_layout)
        
        # RAM
        lbl_ram = QLabel("Memory Allocation")
        lbl_ram.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px; font-weight: 600; letter-spacing: 1px; margin-top: 8px;")
        java_layout.addWidget(lbl_ram)
        
        self.ram_slider = QSlider(Qt.Horizontal)
        self.ram_slider.setMinimum(1024)
        self.ram_slider.setMaximum(16384)
        self.ram_slider.setTickInterval(512)
        self.ram_slider.setSingleStep(512)
        self.ram_slider.setValue(2048)
        self.ram_slider.valueChanged.connect(self.update_ram_label)
        java_layout.addWidget(self.ram_slider)
        
        self.ram_value_label = QLabel("2048 MB (2.0 GB)")
        self.ram_value_label.setAlignment(Qt.AlignCenter)
        self.ram_value_label.setStyleSheet(f"color: {C_GREEN}; font-weight: 600; font-size: 15px;")
        java_layout.addWidget(self.ram_value_label)
        
        java_group.setLayout(java_layout)
        layout.addWidget(java_group)
        
        # --- Game Settings ---
        game_group = QGroupBox("Game")
        game_layout = QVBoxLayout()
        game_layout.setSpacing(10)
        
        lbl_res = QLabel("Resolution")
        lbl_res.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        game_layout.addWidget(lbl_res)
        
        res_layout = QHBoxLayout()
        res_layout.setSpacing(10)
        
        w_label = QLabel("W")
        w_label.setStyleSheet("color: rgba(255,255,255,0.35); font-weight: 600;")
        res_layout.addWidget(w_label)
        self.width_input = QSpinBox()
        self.width_input.setRange(800, 7680)
        self.width_input.setValue(854)
        res_layout.addWidget(self.width_input)
        
        x_label = QLabel("×")
        x_label.setStyleSheet("color: rgba(255,255,255,0.2); font-size: 16px;")
        x_label.setAlignment(Qt.AlignCenter)
        res_layout.addWidget(x_label)
        
        h_label = QLabel("H")
        h_label.setStyleSheet("color: rgba(255,255,255,0.35); font-weight: 600;")
        res_layout.addWidget(h_label)
        self.height_input = QSpinBox()
        self.height_input.setRange(600, 4320)
        self.height_input.setValue(480)
        res_layout.addWidget(self.height_input)
        
        game_layout.addLayout(res_layout)
        
        self.fullscreen_check = QCheckBox("Launch in Fullscreen")
        game_layout.addWidget(self.fullscreen_check)
        
        game_group.setLayout(game_layout)
        layout.addWidget(game_group)

        layout.addStretch()

        # --- Buttons ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.open_folder_button = QPushButton("Open Game Folder")
        self.open_folder_button.setCursor(Qt.PointingHandCursor)
        self.open_folder_button.clicked.connect(self.open_game_folder)
        button_layout.addWidget(self.open_folder_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_GREEN_D};
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                font-size: 14px;
                padding: 10px 28px;
            }}
            QPushButton:hover {{
                background-color: {C_GREEN};
            }}
        """)
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)

        self.load_settings()

    def _on_close(self):
        self.closed.emit()

    def update_ram_label(self, value):
        gb = value / 1024
        self.ram_value_label.setText(f"{value} MB ({gb:.1f} GB)")

    def browse_java(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Java Executable", "", "Executables (*.exe);;All Files (*)")
        if filename:
            self.java_path_input.setText(filename)

    def open_game_folder(self):
        try:
            path = os.path.join(os.getenv('APPDATA'), '.minecraft')
            if not os.path.exists(path):
                os.makedirs(path)
            os.startfile(path)
        except Exception as e:
            print(f"Error opening folder: {e}")

    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    ram = settings.get("max_memory", 2048)
                    self.ram_slider.setValue(int(ram))
                    self.java_path_input.setText(settings.get("java_path", ""))
                    self.width_input.setValue(settings.get("width", 854))
                    self.height_input.setValue(settings.get("height", 480))
                    self.fullscreen_check.setChecked(settings.get("fullscreen", False))
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings = {}
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
            
            settings["max_memory"] = self.ram_slider.value()
            settings["java_path"] = self.java_path_input.text()
            settings["width"] = self.width_input.value()
            settings["height"] = self.height_input.value()
            settings["fullscreen"] = self.fullscreen_check.isChecked()
            
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
                
            self.closed.emit()
        except Exception as e:
            print(f"Error saving settings: {e}")
