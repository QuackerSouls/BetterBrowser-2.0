
import sys
import os
import socket
import json
import urllib.parse
from datetime import datetime
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWebEngineCore import *

class CustomNetworkAccessManager:
    """Handle custom DNS resolution"""
    def __init__(self):
        self.dns_cache = {
            "httpbin.org": "54.91.118.50",
            "example.com": "93.184.216.34",
            "httpforever.com": "195.154.146.186"
        }

    def resolve_host(self, hostname):
        """Resolve hostname using manual DNS first, then system DNS"""
        if hostname in self.dns_cache:
            return self.dns_cache[hostname]
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None

    def add_dns_entry(self, hostname, ip):
        """Add a manual DNS entry"""
        self.dns_cache[hostname] = ip

    def remove_dns_entry(self, hostname):
        """Remove a manual DNS entry"""
        if hostname in self.dns_cache:
            del self.dns_cache[hostname]

    def clear_dns_cache(self):
        """Clear all manual DNS entries"""
        self.dns_cache.clear()

    def get_dns_entries(self):
        """Get all DNS entries"""
        return self.dns_cache.copy()

class BrowserTab(QWebEngineView):
    """Individual browser tab with enhanced functionality"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_browser = parent
        self.is_loading = False

        # Create custom page
        self.custom_page = QWebEnginePage(self)
        self.setPage(self.custom_page)

        # Connect signals
        self.loadStarted.connect(self.on_load_started)
        self.loadFinished.connect(self.on_load_finished)
        self.loadProgress.connect(self.on_load_progress)
        self.urlChanged.connect(self.on_url_changed)
        self.titleChanged.connect(self.on_title_changed)

    def on_load_started(self):
        self.is_loading = True
        if self.parent_browser:
            self.parent_browser.update_status("Loading...")

    def on_load_finished(self, success):
        self.is_loading = False
        if self.parent_browser:
            status = "Ready" if success else "Failed to load page"
            self.parent_browser.update_status(status)

    def on_load_progress(self, progress):
        if self.parent_browser:
            self.parent_browser.update_progress(progress)

    def on_url_changed(self, url):
        if self.parent_browser:
            self.parent_browser.update_url_bar(url.toString())

    def on_title_changed(self, title):
        if self.parent_browser:
            self.parent_browser.update_tab_title(self, title)

class DNSManagerDialog(QDialog):
    """Dialog for managing manual DNS entries"""

    def __init__(self, dns_manager, parent=None):
        super().__init__(parent)
        self.dns_manager = dns_manager
        self.setWindowTitle("DNS Manager")
        self.setModal(True)
        self.resize(600, 400)

        self.setup_ui()
        self.refresh_dns_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Add DNS entry section
        add_group = QGroupBox("Add DNS Entry")
        add_layout = QHBoxLayout(add_group)

        add_layout.addWidget(QLabel("Domain:"))
        self.domain_entry = QLineEdit()
        self.domain_entry.setPlaceholderText("example.com")
        add_layout.addWidget(self.domain_entry)

        add_layout.addWidget(QLabel("IP Address:"))
        self.ip_entry = QLineEdit()
        self.ip_entry.setPlaceholderText("192.168.1.100")
        add_layout.addWidget(self.ip_entry)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_dns_entry)
        add_layout.addWidget(add_btn)

        layout.addWidget(add_group)

        # DNS entries list
        list_group = QGroupBox("Current DNS Entries")
        list_layout = QVBoxLayout(list_group)

        self.dns_list = QTableWidget()
        self.dns_list.setColumnCount(3)
        self.dns_list.setHorizontalHeaderLabels(["Domain", "IP Address", "Action"])
        self.dns_list.horizontalHeader().setStretchLastSection(True)
        self.dns_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        list_layout.addWidget(self.dns_list)

        # Buttons
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all_dns)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        list_layout.addLayout(button_layout)
        layout.addWidget(list_group)

    def add_dns_entry(self):
        domain = self.domain_entry.text().strip()
        ip = self.ip_entry.text().strip()

        if not domain or not ip:
            QMessageBox.warning(self, "Error", "Please enter both domain and IP address")
            return

        # Validate IP address
        try:
            socket.inet_aton(ip)
        except socket.error:
            QMessageBox.warning(self, "Error", "Invalid IP address format")
            return

        self.dns_manager.add_dns_entry(domain, ip)
        self.domain_entry.clear()
        self.ip_entry.clear()
        self.refresh_dns_list()

        QMessageBox.information(self, "Success", f"DNS entry added: {domain} -> {ip}")

    def remove_dns_entry(self, domain):
        reply = QMessageBox.question(self, "Confirm", f"Remove DNS entry for {domain}?")
        if reply == QMessageBox.StandardButton.Yes:
            self.dns_manager.remove_dns_entry(domain)
            self.refresh_dns_list()

    def clear_all_dns(self):
        reply = QMessageBox.question(self, "Confirm", "Clear all DNS entries?")
        if reply == QMessageBox.StandardButton.Yes:
            self.dns_manager.clear_dns_cache()
            self.refresh_dns_list()

    def refresh_dns_list(self):
        entries = self.dns_manager.get_dns_entries()
        self.dns_list.setRowCount(len(entries))

        for row, (domain, ip) in enumerate(entries.items()):
            self.dns_list.setItem(row, 0, QTableWidgetItem(domain))
            self.dns_list.setItem(row, 1, QTableWidgetItem(ip))

            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, d=domain: self.remove_dns_entry(d))
            self.dns_list.setCellWidget(row, 2, remove_btn)

class BookmarksDialog(QDialog):
    """Dialog for managing bookmarks"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmarks Manager")
        self.setModal(True)
        self.resize(600, 400)

        self.bookmarks = self.load_bookmarks()
        self.setup_ui()
        self.refresh_bookmarks_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Add bookmark section
        add_group = QGroupBox("Add Bookmark")
        add_layout = QHBoxLayout(add_group)

        add_layout.addWidget(QLabel("Title:"))
        self.title_entry = QLineEdit()
        add_layout.addWidget(self.title_entry)

        add_layout.addWidget(QLabel("URL:"))
        self.url_entry = QLineEdit()
        add_layout.addWidget(self.url_entry)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_bookmark)
        add_layout.addWidget(add_btn)

        layout.addWidget(add_group)

        # Bookmarks list
        list_group = QGroupBox("Bookmarks")
        list_layout = QVBoxLayout(list_group)

        self.bookmarks_list = QTableWidget()
        self.bookmarks_list.setColumnCount(3)
        self.bookmarks_list.setHorizontalHeaderLabels(["Title", "URL", "Action"])
        self.bookmarks_list.horizontalHeader().setStretchLastSection(True)
        list_layout.addWidget(self.bookmarks_list)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        list_layout.addLayout(button_layout)
        layout.addWidget(list_group)

    def load_bookmarks(self):
        """Load bookmarks from file"""
        bookmarks_file = "bookmarks.json"
        if os.path.exists(bookmarks_file):
            try:
                with open(bookmarks_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return [
            {"title": "Google", "url": "https://www.google.com"},
            {"title": "GitHub", "url": "https://github.com"},
            {"title": "Stack Overflow", "url": "https://stackoverflow.com"}
        ]

    def save_bookmarks(self):
        """Save bookmarks to file"""
        try:
            with open("bookmarks.json", 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")

    def add_bookmark(self):
        title = self.title_entry.text().strip()
        url = self.url_entry.text().strip()

        if not title or not url:
            QMessageBox.warning(self, "Error", "Please enter both title and URL")
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        self.bookmarks.append({"title": title, "url": url})
        self.save_bookmarks()

        self.title_entry.clear()
        self.url_entry.clear()
        self.refresh_bookmarks_list()

    def remove_bookmark(self, index):
        if 0 <= index < len(self.bookmarks):
            self.bookmarks.pop(index)
            self.save_bookmarks()
            self.refresh_bookmarks_list()

    def refresh_bookmarks_list(self):
        self.bookmarks_list.setRowCount(len(self.bookmarks))

        for row, bookmark in enumerate(self.bookmarks):
            self.bookmarks_list.setItem(row, 0, QTableWidgetItem(bookmark["title"]))
            self.bookmarks_list.setItem(row, 1, QTableWidgetItem(bookmark["url"]))

            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, idx=row: self.remove_bookmark(idx))
            self.bookmarks_list.setCellWidget(row, 2, remove_btn)

class MainBrowser(QMainWindow):
    """Main browser window with all features"""

    def __init__(self):
        super().__init__()
        self.dns_manager = CustomNetworkAccessManager()
        self.current_tab_index = 0

        self.setWindowTitle("PyBrowser - Advanced Web Browser")
        self.setMinimumSize(1200, 800)
        self.showMaximized()

        # Apply modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #d0d0d0;
                spacing: 5px;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QStatusBar {
                background-color: #f8f8f8;
                border-top: 1px solid #d0d0d0;
            }
        """)

        self.setup_ui()
        self.create_initial_tab()

    def setup_ui(self):
        """Setup the main user interface"""

        # Central widget with tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        # Create menu bar
        self.create_menu_bar()

        # Create navigation toolbar
        self.create_navigation_toolbar()

        # Create bookmarks toolbar
        self.create_bookmarks_toolbar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # DNS status label
        self.dns_status_label = QLabel("DNS: Ready")
        self.status_bar.addPermanentWidget(self.dns_status_label)

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

        new_window_action = QAction("New Window", self)
        new_window_action.setShortcut("Ctrl+N")
        new_window_action.triggered.connect(self.new_window)
        file_menu.addAction(new_window_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        dns_manager_action = QAction("DNS Manager", self)
        dns_manager_action.triggered.connect(self.open_dns_manager)
        tools_menu.addAction(dns_manager_action)

        bookmarks_action = QAction("Bookmarks Manager", self)
        bookmarks_action.triggered.connect(self.open_bookmarks_manager)
        tools_menu.addAction(bookmarks_action)

        tools_menu.addSeparator()

        dev_tools_action = QAction("Developer Tools", self)
        dev_tools_action.setShortcut("F12")
        dev_tools_action.triggered.connect(self.open_dev_tools)
        tools_menu.addAction(dev_tools_action)

    def create_navigation_toolbar(self):
        """Create the navigation toolbar"""
        nav_toolbar = QToolBar("Navigation")
        nav_toolbar.setMovable(False)
        self.addToolBar(nav_toolbar)

        # Back button
        back_action = QAction("◀", self)
        back_action.setStatusTip("Go back")
        back_action.setShortcut("Alt+Left")
        back_action.triggered.connect(self.navigate_back)
        nav_toolbar.addAction(back_action)

        # Forward button
        forward_action = QAction("▶", self)
        forward_action.setStatusTip("Go forward")
        forward_action.setShortcut("Alt+Right")
        forward_action.triggered.connect(self.navigate_forward)
        nav_toolbar.addAction(forward_action)

        # Reload button
        reload_action = QAction("↻", self)
        reload_action.setStatusTip("Reload page")
        reload_action.setShortcut("F5")
        reload_action.triggered.connect(self.reload_page)
        nav_toolbar.addAction(reload_action)

        # Home button
        home_action = QAction("🏠", self)
        home_action.setStatusTip("Go to home page")
        home_action.setShortcut("Alt+Home")
        home_action.triggered.connect(self.navigate_home)
        nav_toolbar.addAction(home_action)

        # Address bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_toolbar.addWidget(self.url_bar)

        # New tab button
        new_tab_action = QAction("➕", self)
        new_tab_action.setStatusTip("New tab")
        new_tab_action.triggered.connect(self.add_new_tab)
        nav_toolbar.addAction(new_tab_action)

    def create_bookmarks_toolbar(self):
        """Create the bookmarks toolbar"""
        bookmarks_toolbar = QToolBar("Bookmarks")
        bookmarks_toolbar.setMovable(False)
        self.addToolBar(bookmarks_toolbar)

        # Load and add bookmark buttons
        bookmarks_dialog = BookmarksDialog()
        bookmarks = bookmarks_dialog.bookmarks

        for bookmark in bookmarks[:8]:  # Limit to first 8 bookmarks
            bookmark_action = QAction(bookmark["title"], self)
            bookmark_action.setStatusTip(bookmark["url"])
            bookmark_action.triggered.connect(
                lambda checked, url=bookmark["url"]: self.navigate_to_specific_url(url)
            )
            bookmarks_toolbar.addAction(bookmark_action)

    def create_initial_tab(self):
        """Create the first tab"""
        self.add_new_tab("https://www.google.com", "New Tab")

    def add_new_tab(self, url=None, title="New Tab"):
        """Add a new browser tab"""
        browser_tab = BrowserTab(self)

        # Set default URL if none provided
        if url is None:
            url = "https://www.google.com"

        # Add tab to tab widget
        index = self.tabs.addTab(browser_tab, title)
        self.tabs.setCurrentIndex(index)

        # Load the URL
        if url:
            browser_tab.load(QUrl(url))

        return browser_tab

    def close_tab(self, index):
        """Close a tab"""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.close()

    def current_tab_changed(self, index):
        """Handle tab change"""
        self.current_tab_index = index
        current_tab = self.tabs.currentWidget()
        if current_tab:
            self.update_url_bar(current_tab.url().toString())

    def get_current_tab(self):
        """Get the currently active tab"""
        return self.tabs.currentWidget()

    def navigate_back(self):
        """Navigate back in current tab"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.back()

    def navigate_forward(self):
        """Navigate forward in current tab"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.forward()

    def reload_page(self):
        """Reload current page"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.reload()

    def navigate_home(self):
        """Navigate to home page"""
        self.navigate_to_specific_url("https://www.google.com")

    def navigate_to_url(self):
        """Navigate to URL in address bar"""
        url = self.url_bar.text().strip()
        if url:
            self.navigate_to_specific_url(url)

    def navigate_to_specific_url(self, url):
        """Navigate to a specific URL"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        # Process URL
        if not url.startswith(('http://', 'https://')):
            # Check if it's a search query or domain
            if '.' not in url or ' ' in url:
                # Treat as search query
                url = f"https://www.google.com/search?q={urllib.parse.quote(url)}"
            else:
                # Treat as domain
                url = f"https://{url}"

        # Custom DNS resolution for display purposes
        try:
            parsed_url = urllib.parse.urlparse(url)
            hostname = parsed_url.netloc
            if hostname:
                resolved_ip = self.dns_manager.resolve_host(hostname)
                if resolved_ip and hostname in self.dns_manager.dns_cache:
                    self.dns_status_label.setText(f"DNS: {hostname} -> {resolved_ip}")
                else:
                    self.dns_status_label.setText("DNS: System")
        except:
            self.dns_status_label.setText("DNS: Ready")

        # Load the URL
        current_tab.load(QUrl(url))

    def update_url_bar(self, url):
        """Update the address bar"""
        self.url_bar.setText(url)
        self.url_bar.setCursorPosition(0)

    def update_tab_title(self, tab, title):
        """Update tab title"""
        index = self.tabs.indexOf(tab)
        if index >= 0:
            # Limit title length
            if len(title) > 30:
                title = title[:30] + "..."
            self.tabs.setTabText(index, title or "New Tab")

    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.showMessage(message, 3000)

    def update_progress(self, progress):
        """Update loading progress"""
        if progress < 100:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.setVisible(False)

    def open_dns_manager(self):
        """Open DNS manager dialog"""
        dialog = DNSManagerDialog(self.dns_manager, self)
        dialog.exec()

    def open_bookmarks_manager(self):
        """Open bookmarks manager dialog"""
        dialog = BookmarksDialog(self)
        dialog.exec()
        # Refresh bookmarks toolbar after dialog closes
        self.create_bookmarks_toolbar()

    def open_dev_tools(self):
        """Open developer tools for current tab"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.page().setDevToolsPage(current_tab.page())

    def new_window(self):
        """Open a new browser window"""
        new_browser = MainBrowser()
        new_browser.show()

def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PyBrowser")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("PyBrowser Team")

    # Create and show main window
    browser = MainBrowser()
    browser.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
