import sys
import random
import time
import json
import socket
import threading
import hashlib
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import QTcpServer, QTcpSocket, QHostAddress, QNetworkInterface, QAbstractSocket
from flask import Flask, request, jsonify
import psutil
import requests
import os

class LogSignal(QObject):
    log_message = pyqtSignal(str)

class CyberLoaderAPI:
    def __init__(self):
        self.connected = False
        self.status = "disconnected"
        self.version = "3.0.0"
        self.actions = []
        self.server = None
        self.clients = []
        self.command_stats = {}
        self.authenticated = False
        self.encryption_key = None
        self.registered_loaders = {}
        self.http_server = None
        self.registered_loaders_lock = threading.Lock()
        self.actions_lock = threading.Lock()

    def start_servers(self):
        self.server = QTcpServer()
        if not self.server.listen(QHostAddress.Any, 1337):
            print("Failed to start TCP server!")
            return False
        
        threading.Thread(
            target=self.run_http_server,
            daemon=True
        ).start()
        return True
    
    def run_http_server(self):
        app = Flask(__name__)
        
        @app.route('/register', methods=['POST'])
        def register_loader():
            data = request.get_json()
            hardware_id = data.get('hardware_id')
            status = data.get('status')
            if hardware_id and status:
                self.register_loader(hardware_id, status)
                return jsonify({"status": "success"}), 200
            return jsonify({"error": "Invalid data"}), 400
        
        @app.route('/command', methods=['POST'])
        def handle_command():
            if not self.authenticated:
                return jsonify({"error": "Authentication required"}), 401
            data = request.get_json()
            action = data.get('action')
            params = data.get('params', {})
            target = data.get('target')
            if target and target not in self.registered_loaders:
                return jsonify({"error": "Loader not registered"}), 404
            if action == "poll":
                # Для опроса возвращаем последнюю команду для лоудера, если она есть
                last_action = next((a for a in reversed(self.actions) if a.get('target') == target), None)
                if last_action:
                    handler = getattr(self, f"handle_{last_action['action']}", None)
                    if handler:
                        return jsonify(handler(last_action['params'])), 200
                return jsonify({"status": "success", "message": "No new commands"}), 200
            self.log_action(action, params, time.time(), "http", target)
            handler = getattr(self, f"handle_{action}", None)
            if handler:
                return jsonify(handler(params)), 200
            return jsonify({"error": "Unknown action"}), 400
        
        app.run(host='0.0.0.0', port=5000, debug=False)

    def register_loader(self, hardware_id, status):
        with self.registered_loaders_lock:
            self.registered_loaders[hardware_id] = {
                'status': status,
                'last_seen': time.time()
            }

    def get_registered_loaders(self):
        with self.registered_loaders_lock:
            return dict(self.registered_loaders)

    def log_action(self, action, params, timestamp, type, target=None):
        with self.actions_lock:
            action_data = {
                "action": action,
                "params": params,
                "timestamp": timestamp,
                "type": type
            }
            if target:
                action_data["target"] = target
            self.actions.append(action_data)

    def get_action_count(self):
        with self.actions_lock:
            return len(self.actions)

    def get_ip_address(self):
        try:
            interfaces = QNetworkInterface.allInterfaces()
            for interface in interfaces:
                if not interface.flags() & QNetworkInterface.IsLoopBack:
                    for address in interface.addressEntries():
                        if address.ip().protocol() == QAbstractSocket.IPv4Protocol:
                            return address.ip().toString()
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"

    def handle_crash_loader(self, params):
        return {"status": "success", "message": "Crash command sent"}

    def handle_ghost_mode(self, params):
        return {"status": "success", "message": "Ghost mode activated"}

    def handle_squid_game(self, params):
        return {"status": "success", "message": "Squid game mode activated"}

    def handle_shoot_loader(self, params):
        return {"status": "success", "message": "Shooting mode activated"}

    def handle_virtual_party(self, params):
        return {"status": "success", "message": "Virtual party started"}

    def handle_launch_rocket(self, params):
        return {"status": "success", "message": "Rocket launch initiated"}

class CyberLoaderTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ CYBER LOADER TOOLBOX ⚡")
        self.setGeometry(100, 100, 1400, 800)
        
        self.api = CyberLoaderAPI()
        if not self.api.start_servers():
            QMessageBox.critical(self, "Error", "Failed to start API servers!")
            sys.exit(1)
        
        self.log_signal = LogSignal()
        self.log_signal.log_message.connect(self.append_log_message)
        
        self.init_ui()
        
    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.create_left_panel()
        self.create_right_panel()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.log_signal.log_message.emit("🌐 API servers successfully started")
        self.log_signal.log_message.emit(f"TCP: 1337, HTTP: 5000")
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)
    
    def create_left_panel(self):
        self.left_panel = QFrame()
        self.left_panel.setStyleSheet("background: #1a1a2e; border-radius: 15px;")
        
        layout = QVBoxLayout(self.left_panel)
        
        title = QLabel("CYBER LOADER TOOLBOX")
        title.setStyleSheet("font-size: 20px; color: #4cc9f0; font-weight: bold;")
        layout.addWidget(title)
        
        self.server_info = QLabel()
        self.server_info.setStyleSheet("font-size: 14px; color: #ffffff;")
        layout.addWidget(self.server_info)
        
        self.loaders_label = QLabel("Active Loaders:")
        self.loaders_label.setStyleSheet("font-size: 16px; color: #4cc9f0;")
        layout.addWidget(self.loaders_label)
        
        self.loaders_list = QListWidget()
        self.loaders_list.setStyleSheet("""
            QListWidget {
                background: #16213e;
                border: 1px solid #4cc9f0;
                border-radius: 10px;
                color: white;
            }
        """)
        layout.addWidget(self.loaders_list)
        
        self.auth_status = QLabel("Authenticated: No")
        self.auth_status.setStyleSheet("font-size: 14px; color: #ff5555;")
        layout.addWidget(self.auth_status)
        
        self.auth_btn = QPushButton("🔐 Authentication")
        self.auth_btn.setStyleSheet("""
            QPushButton {
                background: #3a0ca3;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background: #4cc9f0;
            }
        """)
        self.auth_btn.clicked.connect(self.show_auth_dialog)
        layout.addWidget(self.auth_btn)
        
        self.main_layout.addWidget(self.left_panel, 30)
    
    def create_right_panel(self):
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("background: #1a1a2e; border-radius: 15px;")
        
        layout = QVBoxLayout(self.right_panel)
        
        title = QLabel("Control Functions")
        title.setStyleSheet("font-size: 20px; color: #4cc9f0; font-weight: bold;")
        layout.addWidget(title)
        
        grid = QGridLayout()
        
        self.prank_buttons = [
            ("💣 Crash", self.crash_loader, "#f72585"),
            ("👻 Ghost", self.ghost_mode, "#7209b7"),
            ("🎮 Squid", self.squid_game, "#3a0ca3"),
            ("🔫 Shoot", self.shoot_loader, "#4361ee"),
            ("🎉 Party", self.virtual_party, "#4cc9f0"),
            ("🚀 Rocket", self.launch_rocket, "#2ec4b6")
        ]
        
        for i, (text, func, color) in enumerate(self.prank_buttons):
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border-radius: 10px;
                    padding: 15px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background: #ffffff;
                    color: {color};
                }}
            """)
            btn.clicked.connect(func)
            grid.addWidget(btn, i // 2, i % 2)
        
        layout.addLayout(grid)
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("""
            QTextEdit {
                background: #16213e;
                border: 1px solid #4cc9f0;
                border-radius: 10px;
                color: white;
                font-family: Consolas;
            }
        """)
        layout.addWidget(self.log_console)
        
        self.main_layout.addWidget(self.right_panel, 70)
    
    def show_auth_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Authentication")
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Enter access token:")
        layout.addWidget(label)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("SECURE_TOKEN_123")
        layout.addWidget(self.token_input)
        
        btn = QPushButton("Confirm")
        btn.clicked.connect(lambda: self.authenticate(dialog))
        layout.addWidget(btn)
        
        dialog.exec_()
    
    def authenticate(self, dialog):
        token = self.token_input.text().strip()
        if not token:
            self.log_signal.log_message.emit("❌ Authentication failed: Empty token")
            QMessageBox.warning(self, "Error", "Token cannot be empty!")
            return
        if token == os.environ.get('AUTH_TOKEN', 'SECURE_TOKEN_123'):
            self.api.authenticated = True
            self.auth_status.setText("Authenticated: Yes")
            self.auth_status.setStyleSheet("font-size: 14px; color: #55ff55;")
            self.log_signal.log_message.emit("🔓 Authentication successful")
            dialog.close()
        else:
            self.log_signal.log_message.emit(f"❌ Authentication failed: Invalid token '{token}'")
            QMessageBox.warning(self, "Error", "Invalid access token! Please enter SECURE_TOKEN_123.")
    
    @pyqtSlot(str)
    def append_log_message(self, message):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_console.append(f"[{timestamp}] {message}")
        self.status_bar.showMessage(message)
    
    def update_ui(self):
        ip = self.api.get_ip_address()
        action_count = self.api.get_action_count()
        self.server_info.setText(f"""
            <b>TCP:</b> {ip}:1337<br>
            <b>HTTP:</b> {ip}:5000<br>
            <b>Status:</b> {self.api.status}<br>
            <b>Commands:</b> {action_count}
        """)
        
        self.loaders_list.clear()
        loaders = self.api.get_registered_loaders()
        for hwid, data in loaders.items():
            status = "🟢" if data['status'] == "запущен" else "🔴"
            self.loaders_list.addItem(f"{status} {hwid} - {data['status']}")
    
    def crash_loader(self):
        if not self.api.authenticated:
            QMessageBox.warning(self, "Error", "Authentication required! Please authenticate first.")
            return
            
        selected = self.loaders_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a loader!")
            return
            
        hwid = selected.text().split()[1]
        self.log_signal.log_message.emit(f"💣 Initiated crash for loader {hwid}...")
        
        threading.Thread(
            target=self.send_http_command,
            args=(hwid, "crash_loader", {}),
            daemon=True
        ).start()
    
    def ghost_mode(self):
        if not self.api.authenticated:
            QMessageBox.warning(self, "Error", "Authentication required! Please authenticate first.")
            return
            
        selected = self.loaders_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a loader!")
            return
            
        hwid = selected.text().split()[1]
        self.log_signal.log_message.emit(f"👻 Initiated ghost mode for loader {hwid}...")
        
        threading.Thread(
            target=self.send_http_command,
            args=(hwid, "ghost_mode", {}),
            daemon=True
        ).start()
    
    def squid_game(self):
        if not self.api.authenticated:
            QMessageBox.warning(self, "Error", "Authentication required! Please authenticate first.")
            return
            
        selected = self.loaders_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a loader!")
            return
            
        hwid = selected.text().split()[1]
        self.log_signal.log_message.emit(f"🎮 Initiated squid game mode for loader {hwid}...")
        
        threading.Thread(
            target=self.send_http_command,
            args=(hwid, "squid_game", {}),
            daemon=True
        ).start()
    
    def shoot_loader(self):
        if not self.api.authenticated:
            QMessageBox.warning(self, "Error", "Authentication required! Please authenticate first.")
            return
            
        selected = self.loaders_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a loader!")
            return
            
        hwid = selected.text().split()[1]
        self.log_signal.log_message.emit(f"🔫 Initiated shooting for loader {hwid}...")
        
        threading.Thread(
            target=self.send_http_command,
            args=(hwid, "shoot_loader", {}),
            daemon=True
        ).start()
    
    def virtual_party(self):
        if not self.api.authenticated:
            QMessageBox.warning(self, "Error", "Authentication required! Please authenticate first.")
            return
            
        selected = self.loaders_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a loader!")
            return
            
        hwid = selected.text().split()[1]
        self.log_signal.log_message.emit(f"🎉 Initiated virtual party for loader {hwid}...")
        
        threading.Thread(
            target=self.send_http_command,
            args=(hwid, "virtual_party", {}),
            daemon=True
        ).start()
    
    def launch_rocket(self):
        if not self.api.authenticated:
            QMessageBox.warning(self, "Error", "Authentication required! Please authenticate first.")
            return
            
        selected = self.loaders_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a loader!")
            return
            
        hwid = selected.text().split()[1]
        self.log_signal.log_message.emit(f"🚀 Initiated rocket launch for loader {hwid}...")
        
        threading.Thread(
            target=self.send_http_command,
            args=(hwid, "launch_rocket", {}),
            daemon=True
        ).start()
    
    def send_http_command(self, hwid, action, params):
        try:
            server_url = os.environ.get('SERVER_URL', 'http://localhost:5000')
            response = requests.post(
                f"{server_url}/command",
                json={
                    "action": action,
                    "params": params,
                    "target": hwid
                },
                headers={"Authorization": os.environ.get('AUTH_TOKEN', 'SECURE_TOKEN_123')},
                timeout=5
            )
            response.raise_for_status()
            self.log_signal.log_message.emit(f"Response from {hwid}: {response.json()}")
        except requests.exceptions.HTTPError as e:
            self.log_signal.log_message.emit(f"HTTP error sending command to {hwid}: {str(e)}")
        except requests.exceptions.ConnectionError:
            self.log_signal.log_message.emit(f"Connection error: Unable to reach server at {server_url}")
        except Exception as e:
            self.log_signal.log_message.emit(f"Error sending command to {hwid}: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = CyberLoaderTool()
    window.show()
    sys.exit(app.exec_())