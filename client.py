#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snakes and Ladders Game - Client Application (GUI)
PyQt5 ile oluşturulan istemci uygulaması
"""

import sys
import socket
import json
import threading
from typing import Optional, Dict, Tuple
from enum import Enum

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGridLayout, QMessageBox, QDialog,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSize, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush, QPen


class GamePhase(Enum):
    """Oyun aşamaları"""
    CONNECTING = "connecting"
    IN_GAME = "in_game"
    FINISHED = "finished"


class CommunicationSignals(QObject):
    """Socket iletişimi için sinyaller"""
    message_received = pyqtSignal(dict)
    connection_failed = pyqtSignal(str)
    connection_established = pyqtSignal()
    disconnected = pyqtSignal(str)


class GameBoardWidget(QWidget):
    """Oyun tahtası görüntüsü"""
    
    BOARD_SIZE = 10
    CELL_SIZE = 60
    LADDERS = {
        4: 38,
        6: 14,
        9: 31,
        13: 36,
        18: 44,
        21: 42,
        28: 58,
        33: 53,
        45: 70,
        51: 67,
        72: 91,
        80: 96,
        94: 98
    }
    
    SNAKES = {
        17: 7,
        27: 11,
        39: 19,
        48: 30,
        54: 34,
        62: 32,
        66: 50,
        78: 57,
        88: 58,
        95: 75,
        97: 79
    }

    PLAYER_COLORS = [
        QColor(231, 76, 60),   # red
        QColor(52, 152, 219),  # blue
        QColor(46, 204, 113),  # green
        QColor(155, 89, 182),  # purple
        QColor(241, 196, 15),  # yellow
    ]

    
    def __init__(self):
        """Tahtayı başlat"""
        super().__init__()
        self.player_positions = {}
        self.current_player = 1
        # keep a reasonable minimum but allow expansion
        self.setMinimumSize(200, 200)

    def cell_size(self) -> int:
        """Hücre boyutunu widget boyutuna göre hesapla"""
        rect = self.contentsRect()
        w = max(1, rect.width())
        h = max(1, rect.height())
        return int(min(w, h) / self.BOARD_SIZE)
    
    def update_positions(self, player_positions: Dict[int, int], current: int):
        """Oyuncu pozisyonlarını güncelle"""
        normalized_positions = {}
        for player_id, position in player_positions.items():
            try:
                normalized_positions[int(player_id)] = int(position)
            except (TypeError, ValueError):
                continue
        self.player_positions = normalized_positions
        self.current_player = current
        self.update()
    
    def pos_to_coords(self, position: int) -> Tuple[int, int]:
        """Pozisyonu koordinatlara dönüştür"""
        if position == 0:
            return (0, 9)
        
        position -= 1
        # Satırlar bir ileri bir geri (yılan gibi) numaralandırılır.
        row = 9 - (position // 10)
        col = position % 10 if (position // 10) % 2 == 0 else 9 - (position % 10)
        return (col, row)
    
    def paintEvent(self, event):
        """Tahtayı çiz"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        cs = self.cell_size()
        rect = self.contentsRect()
        board_px = cs * self.BOARD_SIZE
        # center the board within the widget
        x0 = rect.x() + (rect.width() - board_px) // 2
        y0 = rect.y() + (rect.height() - board_px) // 2
        self._board_origin = (x0, y0)

        # Hücreleri çiz
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                x = x0 + col * cs
                y = y0 + row * cs
                
                # Arka plan rengi
                if (row + col) % 2 == 0:
                    painter.fillRect(x, y, cs, cs, QColor(240, 240, 240))
                else:
                    painter.fillRect(x, y, cs, cs, QColor(255, 255, 255))
                
                # Kenar çizgisi
                painter.drawRect(x, y, cs, cs)
                
                # Pozisyon numarası
                position = self.get_position_from_coords(col, row)
                painter.drawText(x + max(4, cs//10), y + max(12, cs//8), str(position))

        self.draw_special_cells(painter)
        
        radius = max(8, cs // 5)
        x0, y0 = getattr(self, '_board_origin', (0, 0))
        # Aynı hücrede birden fazla oyuncu varsa daireleri kaydır.
        offsets = [
            (cs // 6, cs // 6),
            (cs // 2, cs // 6),
            (cs // 6, cs // 2),
            (cs // 2, cs // 2),
            (cs // 3, cs // 3),
        ]

        cell_groups: Dict[Tuple[int, int], list] = {}
        for player_id, position in sorted(self.player_positions.items()):
            cell_groups.setdefault(self.pos_to_coords(position), []).append(player_id)

        for (col, row), player_ids in cell_groups.items():
            for index, player_id in enumerate(player_ids):
                color = self.PLAYER_COLORS[(player_id - 1) % len(self.PLAYER_COLORS)]
                dx, dy = offsets[index % len(offsets)]
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.black, 1))
                ellipse_x = x0 + col * cs + dx
                ellipse_y = y0 + row * cs + dy
                painter.drawEllipse(ellipse_x, ellipse_y, radius, radius)
                painter.setPen(QPen(Qt.white))
                painter.drawText(ellipse_x, ellipse_y, radius, radius, Qt.AlignCenter, str(player_id))
        
        painter.end()

    def get_player_color(self, player_id: int) -> QColor:
        """Oyuncu için sabit renk döndür"""
        return self.PLAYER_COLORS[(player_id - 1) % len(self.PLAYER_COLORS)]

    def draw_special_cells(self, painter: QPainter):
        """Yılan ve merdiven olan hücreleri küçük işaretlerle göster"""
        font = QFont("Arial", 8, QFont.Bold)
        painter.setFont(font)

        for start, end in self.LADDERS.items():
            self.draw_cell_marker(painter, start, end, QColor(46, 204, 113), f"L {start}->{end}")

        for start, end in self.SNAKES.items():
            self.draw_cell_marker(painter, start, end, QColor(231, 76, 60), f"S {start}->{end}")

    def draw_cell_marker(self, painter: QPainter, start: int, end: int, color: QColor, text: str):
        """Tek hücre için küçük renkli işaret çiz"""
        cs = self.cell_size()
        col, row = self.pos_to_coords(start)
        x0, y0 = getattr(self, '_board_origin', (0, 0))
        x = x0 + col * cs
        y = y0 + row * cs

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        rect_h = max(24, cs // 4)
        rect_w = max(32, min(cs - 8, 80))
        rect_x = x + 4
        rect_y = y + max(18, cs // 5)
        painter.drawRoundedRect(rect_x, rect_y, rect_w, rect_h, 4, 4)

        painter.setPen(QPen(Qt.white))
        painter.setFont(QFont("Arial", max(7, rect_h // 3), QFont.Bold))
        marker_type = "L" if start in self.LADDERS else "S"
        top_text = f"{marker_type} {start}"
        bottom_text = str(end)
        painter.drawText(rect_x, rect_y, rect_w, rect_h // 2, Qt.AlignCenter, top_text)
        painter.drawText(rect_x, rect_y + rect_h // 2, rect_w, rect_h // 2, Qt.AlignCenter, bottom_text)

        arrow_x = rect_x + rect_w - max(10, cs // 8)
        arrow_y = rect_y + rect_h // 2
        arrow_size = max(4, cs // 20)
        painter.setPen(QPen(color, max(2, cs // 30)))
        painter.setBrush(Qt.NoBrush)
        if start in self.LADDERS:
            top_y = arrow_y - arrow_size
            painter.drawLine(arrow_x, arrow_y + arrow_size, arrow_x, top_y)
            painter.drawLine(arrow_x, top_y, arrow_x - arrow_size, top_y + arrow_size)
            painter.drawLine(arrow_x, top_y, arrow_x + arrow_size, top_y + arrow_size)
        else:
            bottom_y = arrow_y + arrow_size
            painter.drawLine(arrow_x, arrow_y - arrow_size, arrow_x, bottom_y)
            painter.drawLine(arrow_x, bottom_y, arrow_x - arrow_size, bottom_y - arrow_size)
            painter.drawLine(arrow_x, bottom_y, arrow_x + arrow_size, bottom_y - arrow_size)
    
    def get_position_from_coords(self, col: int, row: int) -> int:
        """Koordinatlardan pozisyonu al"""
        actual_row = 9 - row
        if actual_row % 2 == 0:
            position = actual_row * 10 + col + 1
        else:
            position = actual_row * 10 + (9 - col) + 1
        return position


class ConnectionDialog(QDialog):
    """Sunucu bağlantısı için diyalog"""
    
    def __init__(self, parent=None):
        """Diyalogu başlat"""
        super().__init__(parent)
        self.server_ip = None
        self.server_port = None
        self.init_ui()
    
    def init_ui(self):
        """UI'yi oluştur"""
        self.setWindowTitle("Sunucuya Bağlan")
        self.setModal(True)
        layout = QVBoxLayout()
        
        # IP adresi
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Sunucu IP Adresi:"))
        self.ip_input = QLineEdit()
        self.ip_input.setText("127.0.0.1")
        self.ip_input.setPlaceholderText("örn: 192.168.1.100")
        ip_layout.addWidget(self.ip_input)
        layout.addLayout(ip_layout)
        
        # Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit()
        self.port_input.setText("5000")
        self.port_input.setPlaceholderText("örn: 5000")
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)
        
        # Bağlan butonu
        connect_btn = QPushButton("Bağlan")
        connect_btn.clicked.connect(self.accept)
        layout.addWidget(connect_btn)
        
        self.setLayout(layout)
    
    def get_connection_details(self) -> Tuple[str, int]:
        """Bağlantı detaylarını al"""
        ip = self.ip_input.text().strip()
        port = int(self.port_input.text().strip())
        return ip, port


class GameClient:
    """Oyun istemcisi - Socket yönetimi"""
    
    def __init__(self, signals: CommunicationSignals):
        """İstemciyi başlat"""
        self.socket = None
        self.signals = signals
        self.connected = False
        self.recv_thread = None
        self.receive_buffer = b""
        self.heartbeat_timer = None
    
    def connect_to_server(self, host: str, port: int) -> bool:
        """Sunucuya bağlan"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.socket.settimeout(15)  # 15 saniye timeout
            self.socket.connect((host, port))
            self.connected = True
            
            # Mesaj alma thread'ini başlat
            self.recv_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.recv_thread.start()

            # Basit ping ile bağlantı kopmasın.
            if self.heartbeat_timer is None:
                self.heartbeat_timer = QTimer()
                self.heartbeat_timer.setInterval(10000)
                self.heartbeat_timer.timeout.connect(self.send_heartbeat)
            self.heartbeat_timer.start()
            
            self.signals.connection_established.emit()
            return True
        
        except socket.timeout:
            self.signals.connection_failed.emit("Sunucuya bağlantı zaman aşımına uğradı (15 saniye)")
            return False
        except Exception as e:
            self.signals.connection_failed.emit(f"Bağlantı hatası: {str(e)}")
            return False
    
    def receive_messages(self):
        """Sunucudan mesaj al"""
        try:
            while self.connected:
                try:
                    while b"\n" not in self.receive_buffer:
                        chunk = self.socket.recv(4096)
                        if not chunk:
                            self.connected = False
                            self.signals.disconnected.emit("Sunucu bağlantısı kapalı")
                            break
                        self.receive_buffer += chunk
                except socket.timeout:
                    # Timeout'u görmezden gel, tekrar dene
                    continue
                
                if not self.receive_buffer:
                    break
                
                # Mesajlar satır sonu ile ayrılıyor.
                while b"\n" in self.receive_buffer:
                    raw_message, self.receive_buffer = self.receive_buffer.split(b"\n", 1)
                    raw_message = raw_message.strip()
                    if not raw_message:
                        continue

                    try:
                        message = json.loads(raw_message.decode("utf-8"))
                        self.signals.message_received.emit(message)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode hatası: {e}")
                        continue
        
        except Exception as e:
            if self.connected:
                self.signals.disconnected.emit(f"Sunucudan ayrıldı: {str(e)}")
            self.connected = False
    
    def send_message(self, message: Dict) -> bool:
        """Sunucuya mesaj gönder"""
        try:
            if not self.connected or not self.socket:
                self.signals.disconnected.emit("Sunucuya bağlı değilsiniz")
                return False
            
            json_message = json.dumps(message, ensure_ascii=False)
            data = (json_message + "\n").encode("utf-8")
            self.socket.sendall(data)
            return True
        
        except socket.timeout:
            self.signals.disconnected.emit("Mesaj gönderme timeout")
            self.connected = False
            return False
        except Exception as e:
            self.signals.disconnected.emit(f"Mesaj gönderme hatası: {str(e)}")
            self.connected = False
            return False

    def send_heartbeat(self):
        """Bağlantıyı canlı tutmak için sessiz ping gönder"""
        if self.connected:
            self.send_message({"type": "ping"})
    
    def disconnect(self):
        """Sunucudan ayrıl"""
        self.connected = False
        if self.heartbeat_timer is not None:
            self.heartbeat_timer.stop()
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


class GameWindow(QMainWindow):
    """Ana oyun penceresi"""
    
    def __init__(self):
        """Pencereyi başlat"""
        super().__init__()
        self.setWindowTitle("Yılanlar ve Merdivenler")
        self.setGeometry(100, 100, 800, 700)
        
        self.game_phase = GamePhase.CONNECTING
        self.player_id = None
        self.total_players = 0
        self.last_winner_id = None
        self.signals = CommunicationSignals()
        self.client = GameClient(self.signals)
        
        # Sinyalleri bağla
        self.signals.message_received.connect(self.on_message_received)
        self.signals.connection_failed.connect(self.on_connection_failed)
        self.signals.connection_established.connect(self.on_connection_established)
        self.signals.disconnected.connect(self.on_disconnected)
        self.reconnect_after_disconnect = False
        
        self.init_ui()
        self.show()
    
    def init_ui(self):
        """UI'yi oluştur"""
        central_widget = QWidget()
        self.central_widget = central_widget
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Üst bilgi satırı
        top_bar = QHBoxLayout()

        self.status_label = QLabel("Bağlanılıyor...")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        top_bar.addWidget(self.status_label)

        self.player_label = QLabel("Oyuncu: -")
        self.player_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.player_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_bar.addWidget(self.player_label)

        layout.addLayout(top_bar)
        
        # Oyun tahtası
        self.game_board = GameBoardWidget()
        self.game_board.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.game_board)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        
        self.roll_dice_btn = QPushButton("Zar At")
        self.roll_dice_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.roll_dice_btn.setEnabled(False)
        self.roll_dice_btn.clicked.connect(self.roll_dice)
        button_layout.addWidget(self.roll_dice_btn)
        
        self.reset_btn = QPushButton("Oyunu Sıfırla")
        self.reset_btn.setFont(QFont("Arial", 12))
        self.reset_btn.setEnabled(False)
        self.reset_btn.clicked.connect(self.reset_game)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        
        # Mesaj etiketi
        footer_layout = QHBoxLayout()

        self.message_label = QLabel("")
        self.message_label.setFont(QFont("Arial", 11))
        footer_layout.addWidget(self.message_label)

        self.player_legend_label = QLabel("Oyuncular: -")
        self.player_legend_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.player_legend_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        footer_layout.addWidget(self.player_legend_label)

        self.players_count_label = QLabel("Oyuncu sayısı: 0")
        self.players_count_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.players_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        footer_layout.addWidget(self.players_count_label)

        layout.addLayout(footer_layout)
        
        central_widget.setLayout(layout)

        # Give the game_board most of the vertical space so it can expand
        layout.setStretch(0, 0)  # top bar
        layout.setStretch(1, 1)  # game board - expands
        layout.setStretch(2, 0)  # buttons
        layout.setStretch(3, 0)  # footer row

        # Kazanan/kaybeden ekranı (başlangıçta gizli)
        self.winner_overlay = QWidget(self.central_widget)
        self.winner_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        self.winner_overlay.hide()
        overlay_layout = QVBoxLayout()
        overlay_layout.setAlignment(Qt.AlignCenter)
        self.winner_label = QLabel("")
        self.winner_label.setStyleSheet("color: white")
        self.winner_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.winner_label.setAlignment(Qt.AlignCenter)
        self.winner_label.setWordWrap(False)
        overlay_layout.addWidget(self.winner_label)
        self.winner_continue_btn = QPushButton("Devam")
        self.winner_continue_btn.setFixedWidth(200)
        self.winner_continue_btn.setFixedHeight(60)
        self.winner_continue_btn.setStyleSheet(
            "QPushButton {"
            "    background-color: #2ecc71;"
            "    color: white;"
            "    font-size: 18px;"
            "    font-weight: bold;"
            "    border: 2px solid #27ae60;"
            "    border-radius: 5px;"
            "    padding: 10px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #27ae60;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #229954;"
            "}"
        )
        self.winner_continue_btn.clicked.connect(self.on_winner_continue)
        overlay_layout.addWidget(self.winner_continue_btn)
        self.winner_overlay.setLayout(overlay_layout)

        # Bağlantı reddi overlay'i
        self.connection_overlay = QWidget(self.central_widget)
        self.connection_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 200);")
        self.connection_overlay.hide()
        connection_layout = QVBoxLayout()
        connection_layout.setAlignment(Qt.AlignCenter)

        self.connection_error_label = QLabel("")
        self.connection_error_label.setStyleSheet("color: white")
        self.connection_error_label.setFont(QFont("Arial", 22, QFont.Bold))
        self.connection_error_label.setAlignment(Qt.AlignCenter)
        self.connection_error_label.setWordWrap(True)
        connection_layout.addWidget(self.connection_error_label)

        self.connection_retry_btn = QPushButton("Tamam")
        self.connection_retry_btn.setFixedWidth(220)
        self.connection_retry_btn.setFixedHeight(60)
        self.connection_retry_btn.setStyleSheet(
            "QPushButton {"
            "    background-color: #3498db;"
            "    color: white;"
            "    font-size: 18px;"
            "    font-weight: bold;"
            "    border: 2px solid #2980b9;"
            "    border-radius: 6px;"
            "    padding: 10px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #2980b9;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #1f6691;"
            "}"
        )
        self.connection_retry_btn.clicked.connect(self.on_connection_error_acknowledged)
        connection_layout.addWidget(self.connection_retry_btn)
        self.connection_overlay.setLayout(connection_layout)
    
    def show_connection_dialog(self):
        """Bağlantı diyalogunu göster"""
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            ip, port = dialog.get_connection_details()
            self.status_label.setText(f"{ip}:{port}'a bağlanılıyor...")
            self.client.connect_to_server(ip, port)
        else:
            self.close()

    def update_player_legend(self, total_players: int):
        """Oyuncu renk göstergesini güncelle"""
        if total_players <= 0:
            self.player_legend_label.setText("Oyuncular: -")
            return

        parts = []
        for player_id in range(1, total_players + 1):
            color = self.game_board.get_player_color(player_id)
            parts.append(
                f'<span style="color: rgb({color.red()}, {color.green()}, {color.blue()});">'
                f'■ Oyuncu {player_id}</span>'
            )
        self.player_legend_label.setText("   ".join(parts))

    def update_player_label_color(self, player_id: Optional[int]):
        """Oyuncu etiketinin rengini oyuncu rengine ayarla"""
        if not player_id:
            self.player_label.setStyleSheet("")
            return

        # Sağ üstteki oyuncu etiketi rengi.
        color = self.game_board.get_player_color(player_id)
        self.player_label.setStyleSheet(
            f"color: rgb({color.red()}, {color.green()}, {color.blue()});"
        )

    def resizeEvent(self, event):
        """Ensure overlay covers the central widget on resize"""
        super().resizeEvent(event)
        try:
            if hasattr(self, 'winner_overlay') and self.winner_overlay is not None:
                self.winner_overlay.setGeometry(self.central_widget.rect())
            if hasattr(self, 'connection_overlay') and self.connection_overlay is not None:
                self.connection_overlay.setGeometry(self.central_widget.rect())
        except Exception:
            pass
    
    def on_connection_established(self):
        """Bağlantı kuruldu"""
        self.game_phase = GamePhase.IN_GAME
        self.status_label.setText("Oyuna katıldınız. Oynuncu numarası bekleniyor...")
        self.message_label.setText("Sunucuya bağlandı.")
        self.players_count_label.setText("Oyuncu sayısı: 1")
    
    def on_connection_failed(self, error: str):
        """Bağlantı başarısız"""
        self.show_connection_error(error, reopen_dialog=True)
    
    def on_disconnected(self, message: str):
        """Bağlantı kesildi"""
        self.game_phase = GamePhase.CONNECTING
        if self.reconnect_after_disconnect:
            self.reconnect_after_disconnect = False
            return
        self.show_connection_error(message, reopen_dialog=True)

    def show_connection_error(self, message: str, reopen_dialog: bool = False):
        """Bağlantı hatasını tam ekran katmanla göster"""
        self.reconnect_after_disconnect = reopen_dialog
        self.roll_dice_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.connection_error_label.setText(f"{message}\n\nServer ve IP seçim ekranına yönlendiriliyorsunuz.")
        self.connection_overlay.setGeometry(self.central_widget.rect())
        self.connection_overlay.show()
        self.connection_overlay.raise_()

    def on_connection_error_acknowledged(self):
        """Bağlantı hatası onaylandığında yeniden bağlanma ekranını aç"""
        self.connection_overlay.hide()
        QTimer.singleShot(0, self.show_connection_dialog)
    
    def on_message_received(self, message: Dict):
        """Sunucudan mesaj alındı"""
        msg_type = message.get("type")
        
        if msg_type == "player_assigned":
            self.player_id = message.get("player_id")
            total_players = message.get("total_players", 1)
            self.total_players = total_players
            self.status_label.setText(f"Oyuncu {self.player_id} olarak bağlandınız")
            self.player_label.setText(f"Oyuncu: {self.player_id}")
            self.update_player_label_color(self.player_id)
            self.players_count_label.setText(f"Oyuncu sayısı: {total_players}")
            self.update_player_legend(total_players)
            if self.player_id == 1:
                can_start = total_players >= 2
                self.roll_dice_btn.setEnabled(can_start)
                if can_start:
                    self.status_label.setText("Oyuna katıldınız. İlk zarı atarak oyunu başlatabilirsiniz.")
                else:
                    self.status_label.setText("Oyuna katıldınız. En az 2 oyuncu bekleniyor...")
            else:
                self.roll_dice_btn.setEnabled(False)
        
        elif msg_type == "connection_rejected":
            error_msg = message.get("message", "Bağlantı reddedildi")
            self.status_label.setText(f"Bağlantı reddedildi: {error_msg}")
            self.roll_dice_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
            self.show_connection_error(error_msg, reopen_dialog=True)
            self.client.disconnect()
        
        elif msg_type == "game_started":
            board_state = message.get("board_state", {})
            self.update_board(board_state)
            self.roll_dice_btn.setEnabled(True)
            self.status_label.setText("Oyun başladı! Sırası gelen oyuncu zar atabilir.")
        
        elif msg_type == "dice_rolled":
            player_id = message.get("player_id")
            dice_value = message.get("dice_value")
            move_result = message.get("move_result", {})
            
            msg_text = f"Oyuncu {player_id} zar attı: {dice_value}\n{move_result.get('message', '')}"
            self.message_label.setText(msg_text)
        
        elif msg_type == "game_finished":
            winner = message.get("winner")
            board_state = message.get("board_state", {})
            # Update board first, then show winner overlay
            if board_state:
                self.update_board(board_state)
            if winner is not None:
                self.game_finished(winner)
        
        elif msg_type == "board_updated":
            board_state = message.get("board_state", {})
            self.update_board(board_state)
            
            # Zar atma butonunu güncelle
            total_players = board_state.get("total_players", 0)
            self.total_players = total_players
            if total_players > 0:
                self.players_count_label.setText(f"Oyuncu sayısı: {total_players}")
                self.update_player_legend(total_players)
            if board_state.get("game_state") == "waiting":
                if self.player_id == 1 and total_players >= 2:
                    self.roll_dice_btn.setEnabled(True)
                    self.status_label.setText("Oyuna katıldınız. İlk zarı atarak oyunu başlatabilirsiniz.")
                else:
                    self.roll_dice_btn.setEnabled(False)
                    if self.player_id == 1:
                        self.status_label.setText("Oyuna katıldınız. En az 2 oyuncu bekleniyor...")
            elif board_state.get("current_player") == self.player_id:
                self.roll_dice_btn.setEnabled(True)
                self.status_label.setText(f"Sıra sizin! (Oyuncu {self.player_id})")
            else:
                self.roll_dice_btn.setEnabled(False)
                self.status_label.setText(f"Bekleme... (Oyuncu {board_state.get('current_player')} oynuyor)")
        
        elif msg_type == "error":
            error_msg = message.get("message", "Bilinmeyen hata")
            self.message_label.setText(f"HATA: {error_msg}")
        
        elif msg_type == "game_reset":
            board_state = message.get("board_state", {})
            self.update_board(board_state)
            self.message_label.setText("Oyun sıfırlandı!")
            self.reset_btn.setEnabled(False)
            self.game_phase = GamePhase.IN_GAME
    
    def update_board(self, board_state: Dict):
        """Tahtayı güncelle"""
        player_positions = board_state.get("player_positions", {})
        if not player_positions:
            player_positions = {}
            if "player1_position" in board_state:
                player_positions[1] = board_state.get("player1_position", 0)
            if "player2_position" in board_state:
                player_positions[2] = board_state.get("player2_position", 0)
        current = board_state.get("current_player", 1)
        
        self.game_board.update_positions(player_positions, current)
    
    def roll_dice(self):
        """Zar at"""
        if not self.client.send_message({"type": "roll_dice"}):
            QMessageBox.critical(self, "Hata", "Sunucuya bağlı değilsiniz")
    
    def reset_game(self):
        """Oyunu sıfırla"""
        reply = QMessageBox.question(
            self,
            "Oyunu Sıfırla",
            "Oyunu baştan mı başlatıyorsunuz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if not self.client.send_message({"type": "reset_game"}):
                QMessageBox.critical(self, "Hata", "Sunucuya bağlı değilsiniz")
    
    def game_finished(self, winner: int):
        """Oyun bitti"""
        if self.game_phase == GamePhase.FINISHED and self.last_winner_id == winner and self.winner_overlay.isVisible():
            return
        self.game_phase = GamePhase.FINISHED
        self.roll_dice_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.winner_continue_btn.setEnabled(True)
        self.last_winner_id = winner

        winner_color = None
        if winner is not None:
            winner_color = self.game_board.get_player_color(winner)

        # Kazanan yazı rengi.
        if winner_color is not None:
            self.winner_label.setStyleSheet(
                f"color: rgb({winner_color.red()}, {winner_color.green()}, {winner_color.blue()});"
            )
        else:
            self.winner_label.setStyleSheet("color: white")

        # Show full-window winner overlay
        if winner == self.player_id:
            self.status_label.setText("🎉 Tebrikler! Kazandınız!")
            self.winner_label.setText("Tebrikler! Kazandınız 🎉")
        else:
            self.status_label.setText(f"Oyun bitti. Oyuncu {winner} kazandı.")
            self.winner_label.setText(f"Kaybettiniz.\nOyuncu {winner} Kazandı 🎉")

        self.message_label.setText("Devam'a basın. Tüm oyuncular basınca oyun sıfırlanır.")
        self.winner_overlay.setGeometry(self.central_widget.rect())
        self.winner_overlay.show()

    def on_winner_continue(self):
        """Kullanıcı 'Devam' butonuna bastığında overlay'i kapat; oyun sıfırlanmadan zar atılmasın"""
        self.winner_overlay.hide()
        self.winner_continue_btn.setEnabled(False)
        # Tüm oyuncular 'Devam' basınca sunucudan sıfırlama iste
        try:
            if hasattr(self, 'client') and self.client and getattr(self.client, 'connected', False):
                self.client.send_message({"type": "continue_after_finish"})
        except Exception:
            pass
    
    def closeEvent(self, event):
        """Pencere kapatılırken"""
        self.client.disconnect()
        event.accept()


def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    window = GameWindow()
    QTimer.singleShot(0, window.show_connection_dialog)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
