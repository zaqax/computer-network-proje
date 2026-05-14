#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snakes and Ladders Game - Server Application
AWS üzerinde çalışacak oyun sunucusu
"""

import socket
import json
import threading
import random
import logging
from typing import Dict, Optional, Tuple
from enum import Enum

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameState(Enum):
    """Oyun durumları"""
    WAITING_FOR_PLAYERS = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class SnakesAndLaddersGame:
    """Snakes and Ladders oyunu mantığı"""
    
    BOARD_SIZE = 100
    
    # Merdivenler (başlangıç: varış)
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
    
    def __init__(self, max_players: int = 5):
        """Oyunu başlat"""
        self.max_players = max_players
        self.player_positions = {}  # Oyuncu ID'si: pozisyon
        self.current_player = 1
        self.game_state = GameState.WAITING_FOR_PLAYERS
        self.winner = None
        
    def is_valid_move(self, player_id: int) -> bool:
        """Oyuncu geçerli mi kontrol et"""
        return player_id in self.player_positions
    
    def roll_dice(self) -> int:
        """Zar at (1-6)"""
        return random.randint(1, 6)
    
    def move_player(self, player_id: int, dice_value: int) -> Dict:
        """Oyuncuyu taşı"""
        if not self.is_valid_move(player_id):
            return {"success": False, "error": "Geçersiz oyuncu ID"}
        
        new_position = self.player_positions[player_id] + dice_value
        
        # Tahta sınırlarını kontrol et
        if new_position > self.BOARD_SIZE:
            new_position = self.player_positions[player_id]
            return {
                "success": True,
                "message": "Zar sonucu tahtayı aşıyor. Tekrar oynayabilirsiniz.",
                "current_position": new_position,
                "is_winner": False
            }
        
        # Merdiven kontrolü
        if new_position in self.LADDERS:
            ladder_end = self.LADDERS[new_position]
            result_msg = f"Merdivene çıktınız! {new_position} -> {ladder_end}"
            new_position = ladder_end
        # Yılan kontrolü
        elif new_position in self.SNAKES:
            snake_end = self.SNAKES[new_position]
            result_msg = f"Yılanla karşılaştınız! {new_position} -> {snake_end}"
            new_position = snake_end
        else:
            result_msg = f"Konumunuz: {new_position}"
        
        self.player_positions[player_id] = new_position
        
        # Kazanma kontrolü
        is_winner = new_position == self.BOARD_SIZE
        if is_winner:
            self.winner = player_id
            self.game_state = GameState.FINISHED
        
        return {
            "success": True,
            "message": result_msg,
            "current_position": new_position,
            "is_winner": is_winner,
            "player_id": player_id
        }
    
    def switch_player(self):
        """Oyuncuyu değiştir"""
        player_ids = sorted(self.player_positions.keys())
        current_index = player_ids.index(self.current_player)
        self.current_player = player_ids[(current_index + 1) % len(player_ids)]

    def remove_player(self, player_id: int) -> Optional[int]:
        """Oyuncuyu oyundan kaldır ve geçerli sıra oyuncusunu geri döndür"""
        if player_id not in self.player_positions:
            return self.current_player if self.current_player in self.player_positions else None

        del self.player_positions[player_id]

        if not self.player_positions:
            self.current_player = 1
            self.game_state = GameState.WAITING_FOR_PLAYERS
            return None

        remaining_players = sorted(self.player_positions.keys())

        if self.current_player == player_id or self.current_player not in self.player_positions:
            for candidate in remaining_players:
                if candidate > player_id:
                    self.current_player = candidate
                    break
            else:
                self.current_player = remaining_players[0]

        if len(self.player_positions) < 2 and self.game_state == GameState.IN_PROGRESS:
            self.game_state = GameState.WAITING_FOR_PLAYERS

        return self.current_player
    
    def get_board_state(self) -> Dict:
        """Tahta durumunu döndür"""
        board_state = {
            "current_player": self.current_player,
            "game_state": self.game_state.value,
            "winner": self.winner,
            "player_positions": self.player_positions,
            "total_players": len(self.player_positions)
        }
        # Eski format ile uyum sağlamak için player1_position ve player2_position ekle
        if 1 in self.player_positions:
            board_state["player1_position"] = self.player_positions[1]
        if 2 in self.player_positions:
            board_state["player2_position"] = self.player_positions[2]
        return board_state
    
    def reset_game(self):
        """Oyunu sıfırla"""
        for player_id in self.player_positions.keys():
            self.player_positions[player_id] = 0
        self.current_player = 1
        self.game_state = GameState.WAITING_FOR_PLAYERS
        self.winner = None


class GameServer:
    """Oyun sunucusu"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5000, max_players: int = 5):
        """Sunucuyu başlat"""
        self.host = host
        self.port = port
        self.max_players = max_players
        self.server_socket = None
        self.clients = {}  # Socket: oyuncu ID
        self.client_buffers = {}
        self.game = SnakesAndLaddersGame(max_players=max_players)
        self.lock = threading.Lock()
        # Oyun bittiğinde herkes devama basana kadar bekle.
        self.reset_waiting_players = set()
        self.reset_expected = 0

    def get_next_player_id(self) -> int:
        """Boşta olan en küçük oyuncu ID'sini bul"""
        used_ids = set(self.game.player_positions.keys())
        for player_id in range(1, self.max_players + 1):
            if player_id not in used_ids:
                return player_id
        return self.max_players + 1
        
    def start(self):
        """Sunucuyu çalıştır"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(2)  # Accept timeout
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_players)
            
            logger.info(f"Sunucu başlatıldı: {self.host}:{self.port}")
            logger.info("İstemcileri bekliyorum...")
            
            self.accept_connections()
            
            # Sunucu çalışmaya devam et
            logger.info("Oyun döngüsü başlatılıyor...")
            while True:
                try:
                    threading.Event().wait(timeout=1)
                except KeyboardInterrupt:
                    logger.info("Sunucu kapatılıyor...")
                    break
            
        except Exception as e:
            logger.error(f"Sunucu hatası: {e}")
        finally:
            self.shutdown()
    
    def accept_connections(self):
        """İstemci bağlantılarını kabul et"""
        while True:
            try:
                # accept() yeni bir TCP bağlantısı bekler.
                client_socket, client_address = self.server_socket.accept()
                client_socket.settimeout(10)  # Client socket timeout
                
                with self.lock:
                    # Oyun devam ediyorsa bağlantıyı reddet
                    if self.game.game_state == GameState.IN_PROGRESS:
                        error_msg = "Oyun devam ediyor"
                        self.send_message(client_socket, {
                            "type": "connection_rejected",
                            "message": error_msg
                        })
                        client_socket.close()
                        logger.info(f"Bağlantı reddedildi ({client_address}): {error_msg}")
                        continue
                    
                    # Maksimum oyuncu sayısına ulaştıysa bağlantıyı reddet
                    if len(self.clients) >= self.max_players:
                        error_msg = "Oyun dolu"
                        self.send_message(client_socket, {
                            "type": "connection_rejected",
                            "message": error_msg
                        })
                        client_socket.close()
                        logger.info(f"Bağlantı reddedildi ({client_address}): {error_msg}")
                        continue
                    
                    player_id = self.get_next_player_id()
                    self.clients[client_socket] = player_id
                    self.client_buffers[client_socket] = b""
                    self.game.player_positions[player_id] = 0
                
                logger.info(f"Oyuncu {player_id} bağlandı: {client_address}")
                
                # Oyuncuya ID gönder
                self.send_message(client_socket, {
                    "type": "player_assigned",
                    "player_id": player_id,
                    "message": f"Oyuncu {player_id} olarak oyuna katıldınız",
                    "total_players": len(self.clients)
                })

                # Lobi durumunu tüm bağlı istemcilere bildir
                self.broadcast({
                    "type": "board_updated",
                    "board_state": self.game.get_board_state()
                })
                
                # İstemci thread'ini başlat
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                thread.start()
                
            except socket.timeout:
                # Accept timeout normal, devam et
                continue
            except Exception as e:
                logger.error(f"Bağlantı kabul hatası: {e}")
    
    def start_game(self):
        """Oyunu başlat (en az 2 oyuncu bağlandığında)"""
        with self.lock:
            if self.game.game_state == GameState.WAITING_FOR_PLAYERS and len(self.clients) >= 2:
                logger.info(f"Oyun başlıyor ({len(self.clients)} oyuncu)...")
                self.game.game_state = GameState.IN_PROGRESS
                self.broadcast({
                    "type": "game_started",
                    "message": "Oyun başladı! Oyuncu 1 zar atabilir.",
                    "board_state": self.game.get_board_state()
                })
    
    def handle_client(self, client_socket: socket.socket):
        """İstemciyi yönet"""
        player_id = self.clients.get(client_socket)
        if not player_id:
            return
        
        try:
            while True:
                # Her istemci için ayrı döngü: mesaj al, işle, cevapla.
                message = self.receive_message(client_socket)
                
                if message is None:
                    logger.info(f"Oyuncu {player_id} mesaj alma başarısız")
                    break
                
                try:
                    response = self.process_message(message, player_id)
                    
                    if response:
                        if response.get("type") == "game_reset":
                            self.broadcast(response)
                        else:
                            self.send_message(client_socket, response)

                        # Kazananı tüm clientlara duyur.
                        if response.get("game_finished"):
                            winner = response.get("winner")
                            self.broadcast({
                                "type": "game_finished",
                                "winner": winner,
                                "message": f"Oyuncu {winner} kazandı.",
                                "board_state": self.game.get_board_state()
                            })
                        
                        # Oyunun durumunu tüm oyunculara gönder
                        if response.get("type") in ["dice_rolled", "game_reset"]:
                            self.broadcast({
                                "type": "board_updated",
                                "board_state": self.game.get_board_state()
                            })
                except Exception as e:
                    logger.error(f"İstemci ({player_id}) mesaj işleme hatası: {e}")
                    try:
                        self.send_message(client_socket, {
                            "type": "error",
                            "message": f"Sunucu hatası: {str(e)}"
                        })
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"İstemci ({player_id}) thread hatası: {e}")
        finally:
            self.disconnect_client(client_socket, player_id)
    
    def process_message(self, message: Dict, player_id: int) -> Optional[Dict]:
        """İstemciden gelen mesajı işle"""
        try:
            msg_type = message.get("type")

            if msg_type == "ping":
                return {"type": "pong"}
            
            if msg_type == "roll_dice":
                # Oyun henüz başlamadıysa ve en az 2 oyuncu varsa, başlat
                if self.game.game_state == GameState.WAITING_FOR_PLAYERS:
                    if len(self.clients) >= 2:
                        self.start_game()
                    else:
                        return {"type": "error", "message": "En az 2 oyuncu gelmesi gerekiyor"}
                
                # Oyun bitmişse zar atılamaz
                if self.game.game_state == GameState.FINISHED:
                    return {"type": "error", "message": "Oyun bitmiş. Lütfen oyunu sıfırlayın."}

                # Sadece mevcut oyuncu zar atabilir
                if player_id != self.game.current_player:
                    return {
                        "type": "error",
                        "message": f"Sıra Oyuncu {self.game.current_player}'ında"
                    }

                dice_value = self.game.roll_dice()
                move_result = self.game.move_player(player_id, dice_value)
                
                logger.info(f"Oyuncu {player_id} zar attı: {dice_value} -> {move_result}")
                
                response = {
                    "type": "dice_rolled",
                    "player_id": player_id,
                    "dice_value": dice_value,
                    "move_result": move_result
                }
                
                if move_result.get("is_winner"):
                    response["game_finished"] = True
                    response["winner"] = player_id
                    # Yeni turun başlaması için herkesin devama basması gerek.
                    self.reset_waiting_players = set()
                    self.reset_expected = len(self.clients)
                else:
                    self.game.switch_player()
                
                return response
            
            elif msg_type == "request_board_state":
                return {
                    "type": "board_state",
                    "board_state": self.game.get_board_state()
                }
            
            elif msg_type == "reset_game":
                self.game.reset_game()
                self.reset_waiting_players = set()
                self.reset_expected = 0
                return {
                    "type": "game_reset",
                    "message": "Oyun sıfırlandı",
                    "board_state": self.game.get_board_state()
                }

            elif msg_type == "continue_after_finish":
                if self.game.game_state != GameState.FINISHED:
                    return {"type": "error", "message": "Oyun bitmedi"}

                if self.reset_expected <= 0:
                    self.reset_expected = len(self.clients)

                # Bu oyuncu devama bastı.
                self.reset_waiting_players.add(player_id)

                if self.reset_expected > 0 and len(self.reset_waiting_players) >= self.reset_expected:
                    self.game.reset_game()
                    self.reset_waiting_players = set()
                    self.reset_expected = 0
                    return {
                        "type": "game_reset",
                        "message": "Oyun sıfırlandı",
                        "board_state": self.game.get_board_state()
                    }

                return None
            
            else:
                return {"type": "error", "message": "Bilinmeyen mesaj türü"}
        
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {e}")
            return {"type": "error", "message": str(e)}
    
    def send_message(self, client_socket: socket.socket, message: Dict):
        """İstemciye JSON mesaj gönder"""
        try:
            # TCP stream üzerinde \n ile mesaj sınırı koyuyoruz.
            json_message = json.dumps(message, ensure_ascii=False)
            data = (json_message + "\n").encode("utf-8")
            client_socket.sendall(data)
            logger.debug(f"Mesaj gönderildi: {message.get('type')}")
        except socket.timeout:
            logger.error("Mesaj gönderme timeout")
            raise
        except Exception as e:
            logger.error(f"Mesaj gönderme hatası: {e}")
            raise
    
    def receive_message(self, client_socket: socket.socket) -> Optional[Dict]:
        """İstemciden JSON mesaj al"""
        try:
            buffer = self.client_buffers.get(client_socket, b"")
            while b"\n" not in buffer:
                try:
                    # Parça parça gelen veriyi buffer'da biriktiriyoruz.
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        logger.warning("İstemci bağlantısı kesildi (empty chunk)")
                        return None
                    buffer += chunk
                except socket.timeout:
                    # Timeout'u görmezden gel, tekrar dene
                    continue
            raw_message, remainder = buffer.split(b"\n", 1)
            self.client_buffers[client_socket] = remainder

            message_str = raw_message.decode("utf-8").strip()
            message = json.loads(message_str)
            logger.debug(f"Mesaj alındı: {message.get('type')}")
            return message
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Mesaj alma hatası: {e}")
            return None
    
    def broadcast(self, message: Dict):
        """Tüm istemcilere mesaj gönder"""
        # Sunucudan tüm clientlara aynı mesajı yolluyoruz.
        for client_socket in list(self.clients.keys()):
            try:
                self.send_message(client_socket, message)
            except Exception as e:
                logger.error(f"Broadcast hatası: {e}")
    
    def disconnect_client(self, client_socket: socket.socket, player_id: int):
        """İstemciyi bağlantısını kes"""
        try:
            next_player = None
            was_in_progress = self.game.game_state == GameState.IN_PROGRESS
            with self.lock:
                if client_socket in self.clients:
                    del self.clients[client_socket]
                if client_socket in self.client_buffers:
                    del self.client_buffers[client_socket]
                next_player = self.game.remove_player(player_id)
                if self.game.game_state == GameState.FINISHED:
                    # Oyuncu ayrıldıysa devam etmek isteyenler listesinden çıkarıyoruz.
                    self.reset_waiting_players.discard(player_id)
                    self.reset_expected = len(self.clients)
            
            client_socket.close()
            logger.info(f"Oyuncu {player_id} bağlantısı kesildi")

            if self.game.player_positions:
                if next_player is not None:
                    logger.info(f"Sıra güncellendi: Oyuncu {next_player}")
                # Eğer sadece bir oyuncu kaldıysa, onu kazanan ilan et
                if len(self.game.player_positions) == 1 and was_in_progress:
                    remaining = next(iter(self.game.player_positions.keys()))
                    self.game.winner = remaining
                    self.game.game_state = GameState.FINISHED
                    self.reset_waiting_players = set()
                    self.reset_expected = len(self.clients)
                    logger.info(f"Oyuncu {remaining} rakiplerin ayrılması nedeniyle kazandı.")
                    # Broadcast game_finished explicitly
                    self.broadcast({
                        "type": "game_finished",
                        "winner": remaining,
                        "message": f"Oyuncu {remaining} kazandı (diğerleri ayrıldı).",
                        "board_state": self.game.get_board_state()
                    })
                elif self.game.game_state == GameState.FINISHED:
                    if self.reset_expected > 0 and len(self.reset_waiting_players) >= self.reset_expected:
                        self.game.reset_game()
                        self.reset_waiting_players = set()
                        self.reset_expected = 0
                        self.broadcast({
                            "type": "game_reset",
                            "message": "Oyun sıfırlandı",
                            "board_state": self.game.get_board_state()
                        })
                        self.broadcast({
                            "type": "board_updated",
                            "board_state": self.game.get_board_state()
                        })
                    else:
                        self.broadcast({
                            "type": "board_updated",
                            "board_state": self.game.get_board_state()
                        })
                else:
                    self.broadcast({
                        "type": "board_updated",
                        "board_state": self.game.get_board_state()
                    })
            else:
                self.broadcast({
                    "type": "board_updated",
                    "board_state": self.game.get_board_state()
                })
        except Exception as e:
            logger.error(f"Bağlantı kesme hatası: {e}")
    
    def shutdown(self):
        """Sunucuyu kapat"""
        if self.server_socket:
            self.server_socket.close()
        logger.info("Sunucu kapatıldı")


if __name__ == "__main__":
    server = GameServer(host='0.0.0.0', port=5000)
    server.start()
