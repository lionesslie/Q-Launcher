import os
import requests
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QListWidget, QListWidgetItem, QLabel, QMessageBox,
    QSplitter, QComboBox, QCheckBox, QTextBrowser, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPixmap, QImage, QIcon
from .mod_manager import ModrinthBackend, CurseForgeBackend


class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(str, QPixmap)

    def __init__(self, url, mod_id):
        super().__init__()
        self.url = url
        self.mod_id = mod_id

    def run(self):
        try:
            if not self.url:
                return
            response = requests.get(self.url)
            response.raise_for_status()
            image = QImage()
            image.loadFromData(response.content)
            pixmap = QPixmap(image)
            self.image_loaded.emit(self.mod_id, pixmap)
        except:
            pass


class SearchThread(QThread):
    results_signal = pyqtSignal(list)

    def __init__(self, backend, query, version=None, loader=None, index="relevance", category=None):
        super().__init__()
        self.backend = backend
        self.query = query
        self.version = version
        self.loader = loader
        self.index = index
        self.category = category

    def run(self):
        hits = self.backend.search_mods(self.query, self.version, self.loader, index=self.index, category=self.category)
        self.results_signal.emit(hits)


class ModVersionThread(QThread):
    versions_signal = pyqtSignal(list)

    def __init__(self, backend, mod_slug):
        super().__init__()
        self.backend = backend
        self.slug = mod_slug

    def run(self):
        versions = self.backend.get_mod_versions(self.slug)
        self.versions_signal.emit(versions)


class ModDownloadThread(QThread):
    finished_signal = pyqtSignal(bool, str)
    progress_signal = pyqtSignal(int, int)

    def __init__(self, backend, url, filename):
        super().__init__()
        self.backend = backend
        self.url = url
        self.filename = filename

    def run(self):
        try:
             path = os.path.join(self.backend.mods_directory, self.filename)
             response = requests.get(self.url, stream=True)
             response.raise_for_status()
             
             total_size = int(response.headers.get('content-length', 0))
             downloaded = 0
             
             with open(path, 'wb') as f:
                 for chunk in response.iter_content(chunk_size=8192):
                     f.write(chunk)
                     downloaded += len(chunk)
                     if total_size > 0:
                         self.progress_signal.emit(downloaded, total_size)
             
             self.finished_signal.emit(True, path)
        except Exception as e:
             self.finished_signal.emit(False, str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Design Tokens
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
C_GREEN = "#4ade80"
C_GREEN_D = "#22c55e"
C_GREEN_DD = "#16a34a"
C_ORANGE = "#f97316"
C_ORANGE_D = "#ea580c"


class ModManagerPanel(QWidget):
    closed = pyqtSignal()

    def __init__(self, minecraft_directory, parent=None, current_version=None, current_loader=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("modManagerRoot")

        self.setStyleSheet(f"""
            QWidget#modManagerRoot {{
                background-color: rgba(11, 11, 11, 0.92);
                color: #e8e8e8;
                font-family: {FONT};
            }}
            QWidget#modManagerRoot QWidget {{
                background: transparent;
                color: #e8e8e8;
                font-family: {FONT};
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
            QPushButton {{
                background-color: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                color: white;
                padding: 9px 18px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.15);
            }}
            QPushButton:disabled {{
                background-color: rgba(255,255,255,0.02);
                color: rgba(255,255,255,0.25);
                border: 1px solid rgba(255,255,255,0.04);
            }}
            QListWidget {{
                background-color: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 10px;
                outline: none;
                color: white;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px;
                color: white;
            }}
            QListWidget::item:selected {{
                background-color: rgba(74, 222, 128, 0.12);
                border: 1px solid rgba(74, 222, 128, 0.2);
            }}
            QListWidget::item:hover {{
                background-color: rgba(255,255,255,0.04);
            }}
            QComboBox {{
                background-color: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                min-width: 90px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border: 1px solid rgba(255,255,255,0.18);
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ image: none; }}
            QComboBox QAbstractItemView {{
                background-color: #1c1c1c;
                color: white;
                selection-background-color: {C_GREEN_DD};
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }}
            QCheckBox {{
                spacing: 8px;
                color: rgba(255,255,255,0.6);
                font-size: 12px;
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
            QTextBrowser {{
                background-color: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 10px;
                padding: 14px;
                color: #ccc;
                font-size: 13px;
                line-height: 1.5;
            }}
            QSplitter::handle {{
                background-color: rgba(255,255,255,0.04);
                width: 1px;
                margin: 8px 6px;
            }}
            QLabel {{
                color: #ddd;
            }}
        """)
        
        self.current_version = current_version
        if current_version and "No versions" in current_version:
            self.current_version = None
        self.current_loader = current_loader
        
        # Backends
        self.mods_dir = minecraft_directory
        if not os.path.exists(self.mods_dir):
            os.makedirs(self.mods_dir)
        self.modrinth_backend = ModrinthBackend(self.mods_dir)
        self.curseforge_backend = CurseForgeBackend(self.mods_dir)
        self.active_backend = self.modrinth_backend
        self.active_source = "modrinth"
        
        self.image_cache = {}
        
        # ── Main horizontal layout ──
        main_h = QHBoxLayout(self)
        main_h.setContentsMargins(0, 0, 0, 0)
        main_h.setSpacing(0)
        
        # ━━━ Left Source Panel ━━━
        source_panel = QWidget()
        source_panel.setFixedWidth(180)
        source_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(255,255,255,0.02);
                border-right: 1px solid rgba(255,255,255,0.06);
            }
        """)
        sp_layout = QVBoxLayout(source_panel)
        sp_layout.setContentsMargins(12, 20, 12, 16)
        sp_layout.setSpacing(6)
        
        src_title = QLabel("Sources")
        src_title.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 10px; font-weight: 600; letter-spacing: 1.5px; border: none; background: transparent;")
        sp_layout.addWidget(src_title)
        
        sp_layout.addSpacing(4)
        
        # Modrinth button
        self.modrinth_btn = QPushButton("🟢  Modrinth")
        self.modrinth_btn.setCursor(Qt.PointingHandCursor)
        self.modrinth_btn.clicked.connect(lambda: self._switch_source("modrinth"))
        sp_layout.addWidget(self.modrinth_btn)
        
        # CurseForge button
        self.curseforge_btn = QPushButton("🟠  CurseForge")
        self.curseforge_btn.setCursor(Qt.PointingHandCursor)
        self.curseforge_btn.clicked.connect(lambda: self._switch_source("curseforge"))
        sp_layout.addWidget(self.curseforge_btn)
        
        sp_layout.addStretch()
        
        # Source info
        self.source_info = QLabel("Modrinth\nOpen source\nmod platform")
        self.source_info.setStyleSheet("color: rgba(255,255,255,0.2); font-size: 11px; border: none; background: transparent;")
        self.source_info.setWordWrap(True)
        sp_layout.addWidget(self.source_info)
        
        main_h.addWidget(source_panel)
        
        self._update_source_buttons()
        
        # ━━━ Right Content Area ━━━
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 16)
        content_layout.setSpacing(14)
        
        # ── Title ──
        title_row = QHBoxLayout()
        back_btn = QPushButton("← Geri")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.15);
            }
        """)
        back_btn.clicked.connect(lambda: self.closed.emit())
        title_row.addWidget(back_btn)
        title_row.addSpacing(12)
        header = QLabel("Mod Manager")
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: white; background: transparent; letter-spacing: 0.5px;")
        title_row.addWidget(header)
        self.source_badge = QLabel("Modrinth")
        self.source_badge.setFixedHeight(22)
        self._style_badge("modrinth")
        title_row.addWidget(self.source_badge, 0, Qt.AlignVCenter)
        title_row.addStretch()
        content_layout.addLayout(title_row)

        # ── Search Bar ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search mods...")
        self.search_input.returnPressed.connect(self.search_mods)
        top_bar.addWidget(self.search_input, 2)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Adventure", "Technology", "Magic", "Utility", "Decoration", "Storage", "World Gen", "Optimization"])
        self.category_combo.currentTextChanged.connect(lambda: self.search_mods())
        top_bar.addWidget(self.category_combo)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Relevance", "Downloads", "Newest", "Updated"])
        self.sort_combo.setCurrentText("Relevance")
        self.sort_combo.currentTextChanged.connect(lambda: self.search_mods())
        top_bar.addWidget(self.sort_combo)
        
        self.search_button = QPushButton("Search")
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.clicked.connect(self.search_mods)
        top_bar.addWidget(self.search_button)
        
        content_layout.addLayout(top_bar)
        
        # ── Filter ──
        filter_layout = QHBoxLayout()
        self.filter_check = QCheckBox(f"Filter: {self.current_version} · {self.current_loader}")
        if self.current_version and self.current_loader:
            self.filter_check.setChecked(False)
        else:
            self.filter_check.setEnabled(False)
        self.filter_check.stateChanged.connect(lambda: self.search_mods())
        filter_layout.addWidget(self.filter_check)
        filter_layout.addStretch()
        content_layout.addLayout(filter_layout)
        
        # ── Splitter ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setIconSize(QSize(56, 56))
        self.results_list.itemClicked.connect(self.on_mod_selected)
        splitter.addWidget(self.results_list)
        
        # Details panel
        self.details_panel = QWidget()
        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(16, 0, 0, 0)
        details_layout.setSpacing(12)
        
        # Mod Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(72, 72)
        self.icon_label.setStyleSheet("border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.03); border-radius: 12px;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.icon_label)
        
        title_info = QVBoxLayout()
        title_info.setSpacing(4)
        self.title_label = QLabel("Select a mod")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: white;")
        self.author_label = QLabel("")
        self.author_label.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px;")
        self.download_count_label = QLabel("")
        self.download_count_label.setStyleSheet(f"color: {C_GREEN}; font-weight: 600; font-size: 12px;")
        title_info.addWidget(self.title_label)
        title_info.addWidget(self.author_label)
        title_info.addWidget(self.download_count_label)
        title_info.addStretch()
        header_layout.addLayout(title_info)
        
        details_layout.addLayout(header_layout)
        
        # Description
        self.description_browser = QTextBrowser()
        details_layout.addWidget(self.description_browser)
        
        # Install Bar
        install_bar = QWidget()
        install_bar.setStyleSheet("background-color: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 6px;")
        install_layout = QHBoxLayout(install_bar)
        install_layout.setContentsMargins(12, 8, 12, 8)
        install_layout.setSpacing(10)
        ver_lbl = QLabel("Version")
        ver_lbl.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        install_layout.addWidget(ver_lbl)
        self.version_combo = QComboBox()
        self.version_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        install_layout.addWidget(self.version_combo, 1)
        
        self.install_button = QPushButton("Install")
        self.install_button.setEnabled(False)
        self.install_button.setCursor(Qt.PointingHandCursor)
        self.install_button.clicked.connect(self.download_mod)
        self.install_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_GREEN_D};
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                padding: 10px 24px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {C_GREEN};
            }}
            QPushButton:disabled {{
                background-color: rgba(255,255,255,0.04);
                color: rgba(255,255,255,0.25);
            }}
        """)
        install_layout.addWidget(self.install_button)
        
        details_layout.addWidget(install_bar)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255,255,255,0.03);
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {C_GREEN};
                border-radius: 2px;
            }}
        """)
        details_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(self.details_panel)
        splitter.setSizes([400, 560])
        
        content_layout.addWidget(splitter)
        
        # Status
        self.status_label = QLabel("Loading mods...")
        self.status_label.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 11px;")
        content_layout.addWidget(self.status_label)
        
        main_h.addWidget(content)
        
        # Auto-search on open
        QTimer.singleShot(300, self._auto_search)

    # ── Source Switching ──
    def _switch_source(self, source):
        self.active_source = source
        if source == "modrinth":
            self.active_backend = self.modrinth_backend
            self.source_info.setText("Modrinth\nOpen source\nmod platform")
        else:
            self.active_backend = self.curseforge_backend
            self.source_info.setText("CurseForge\nLargest mod\nrepository")
        self._update_source_buttons()
        self._style_badge(source)
        self.results_list.clear()
        self.search_mods()

    def _update_source_buttons(self):
        active_ss = f"""
            QPushButton {{
                background-color: rgba(74, 222, 128, 0.10);
                border: 1px solid rgba(74, 222, 128, 0.2);
                border-radius: 8px;
                color: white;
                font-weight: 600;
                padding: 10px 14px;
                text-align: left;
            }}
        """
        inactive_ss = f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
                color: rgba(255,255,255,0.5);
                font-weight: 500;
                padding: 10px 14px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.04);
                color: white;
            }}
        """
        self.modrinth_btn.setStyleSheet(active_ss if self.active_source == "modrinth" else inactive_ss)
        self.curseforge_btn.setStyleSheet(active_ss.replace("74, 222, 128", "249, 115, 22") if self.active_source == "curseforge" else inactive_ss)

    def _style_badge(self, source):
        if source == "modrinth":
            color = C_GREEN
            rgba = "74, 222, 128"
            text = "Modrinth"
        else:
            color = C_ORANGE
            rgba = "249, 115, 22"
            text = "CurseForge"
        self.source_badge.setText(text)
        self.source_badge.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 10px;
                font-weight: bold;
                background: rgba({rgba}, 0.10);
                border: 1px solid rgba({rgba}, 0.2);
                border-radius: 11px;
                padding: 0 10px;
            }}
        """)

    def _auto_search(self):
        """Trigger initial search when dialog opens."""
        self.search_mods("")

    # ── Search ──
    def search_mods(self, query=None):
        if query is None:
            query = self.search_input.text()
        
        self.search_button.setEnabled(False)
        self.status_label.setText("Searching...")
        self.results_list.clear()
        
        version_filter = self.current_version if self.filter_check.isChecked() else None
        loader_filter = self.current_loader if self.filter_check.isChecked() else None
        
        sort_mode = self.sort_combo.currentText().lower()
        
        category_text = self.category_combo.currentText()
        category = None
        if category_text != "All":
            category = category_text.lower()
            if category == "world gen":
                category = "worldgen"
            
        self.search_thread = SearchThread(self.active_backend, query, version_filter, loader_filter, index=sort_mode, category=category)
        self.search_thread.results_signal.connect(self.on_search_finished)
        self.search_thread.start()

    def on_search_finished(self, results):
        self.search_button.setEnabled(True)
        self.status_label.setText(f"Found {len(results)} results.")
        
        for mod in results:
            item = QListWidgetItem(f"{mod['title']}")
            item.setToolTip(mod.get('description', ''))
            item.setData(Qt.UserRole, mod)
            self.results_list.addItem(item)
            
            icon_url = mod.get('icon_url')
            if icon_url:
                if icon_url in self.image_cache:
                    item.setIcon(QIcon(self.image_cache[icon_url]))
                else:
                    loader = ImageLoaderThread(icon_url, mod['slug'])
                    loader.image_loaded.connect(self.on_icon_loaded)
                    loader.start()
                    if not hasattr(self, 'icon_loaders'):
                        self.icon_loaders = []
                    self.icon_loaders.append(loader)

    def on_icon_loaded(self, mod_slug, pixmap):
        for i in range(self.results_list.count()):
             item = self.results_list.item(i)
             data = item.data(Qt.UserRole)
             if data['slug'] == mod_slug:
                 item.setIcon(QIcon(pixmap))
                 self.image_cache[data.get('icon_url')] = pixmap
                 
    def on_mod_selected(self, item):
        mod = item.data(Qt.UserRole)
        self.title_label.setText(mod['title'])
        self.author_label.setText(f"By: {mod['author']}")
        
        downloads = mod.get('downloads', 0)
        if downloads >= 1000000:
            dl_text = f"{downloads/1000000:.1f}M downloads"
        elif downloads >= 1000:
            dl_text = f"{downloads/1000:.0f}K downloads"
        else:
            dl_text = f"{downloads} downloads"
        self.download_count_label.setText(dl_text)
        self.description_browser.setText(mod.get('description', 'No description.'))
        
        icon_url = mod.get('icon_url')
        if icon_url and icon_url in self.image_cache:
            self.icon_label.setPixmap(self.image_cache[icon_url].scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.icon_label.clear()
            self.icon_label.setText("No Icon")

        self.version_combo.clear()
        self.version_combo.addItem("Loading versions...")
        self.install_button.setEnabled(False)
        
        slug_or_id = mod.get('project_id', mod.get('slug', ''))
        self.version_thread = ModVersionThread(self.active_backend, slug_or_id)
        self.version_thread.versions_signal.connect(self.on_versions_loaded)
        self.version_thread.start()

    def on_versions_loaded(self, versions):
        self.version_combo.clear()
        
        filtered = versions
        if self.filter_check.isChecked() and self.current_version and self.current_loader:
             target_loader = self.current_loader.lower()
             filtered = [v for v in versions if self.current_version in v.get('game_versions', []) and target_loader in v.get('loaders', [])]
        
        if not filtered:
             self.version_combo.addItem("No compatible versions found")
             self.install_button.setEnabled(False)
             return

        for v in filtered:
            self.version_combo.addItem(f"{v['name']} ({v['version_number']})", v)
        
        self.install_button.setEnabled(True)

    def download_mod(self):
        version_data = self.version_combo.currentData()
        if not version_data:
            return
        
        files = version_data.get('files', [])
        if not files:
            return
        
        primary = next((f for f in files if f.get('primary')), files[0])
        url = primary['url']
        filename = primary['filename']
        
        self.install_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Downloading {filename}...")
        
        self.dl_thread = ModDownloadThread(self.active_backend, url, filename)
        self.dl_thread.progress_signal.connect(self.on_download_progress)
        self.dl_thread.finished_signal.connect(self.on_download_finished)
        self.dl_thread.start()

    def on_download_progress(self, downloaded, total):
        if total > 0:
            self.progress_bar.setValue(int((downloaded / total) * 100))

    def on_download_finished(self, success, result):
        self.install_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        if success:
            self.status_label.setText(f"Installed: {os.path.basename(result)}")
            QMessageBox.information(self, "Success", "Mod installed successfully!")
        else:
            self.status_label.setText("Download Failed")
            QMessageBox.critical(self, "Error", f"Download failed: {result}")
