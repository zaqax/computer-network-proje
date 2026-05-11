# Snakes and Ladders - Geliştirme Kılavuzu

## 📚 Kod Yapısı

### server.py - Sunucu Uygulaması

#### Sınıflar

##### 1. `GameState` (Enum)
Oyun durumlarını tanımlar.

```python
class GameState(Enum):
    WAITING_FOR_PLAYERS = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
```

##### 2. `SnakesAndLaddersGame`
Oyun mantığını yönetir.

**Önemli Metotlar:**
- `roll_dice()`: 1-6 arası rastgele sayı döndürür
- `move_player(player_id, dice_value)`: Oyuncuyu taşır, merdiven/yılan kontrolü yapar
- `switch_player()`: Oyuncu sırasını değiştirir
- `get_board_state()`: Tahta durumunu JSON olarak döndürür

**Örnek Kullanım:**
```python
game = SnakesAndLaddersGame()
dice = game.roll_dice()  # 1-6
result = game.move_player(1, dice)
if result['is_winner']:
    print("Oyuncu 1 kazandı!")
```

##### 3. `GameServer`
TCP sunucusu ve istemci yönetimi.

**Önemli Metotlar:**
- `start()`: Sunucuyu başlatır
- `accept_connections()`: İstemcileri kabul eder
- `handle_client(socket)`: İstemciyi thread'de yönetir
- `broadcast(message)`: Tüm istemcilere mesaj gönderir
- `send_message(socket, message)`: JSON mesaj gönderir
- `receive_message(socket)`: JSON mesaj alır

**Thread Modeli:**
```
Main Thread
    ├─ accept_connections() [Bağlantı kabul]
    └─ handle_client() [Her istemci için ayrı thread]
        └─ receive_messages() [İstemcisinde thread]
```

---

### client.py - İstemci Uygulaması

#### Sınıflar

##### 1. `CommunicationSignals` (QObject)
PyQt5 sinyalleri için.

```python
message_received = pyqtSignal(dict)      # Mesaj alındığında
connection_failed = pyqtSignal(str)      # Bağlantı başarısız
connection_established = pyqtSignal()    # Bağlantı kuruldu
disconnected = pyqtSignal(str)           # Bağlantı kesildi
```

##### 2. `GameBoardWidget` (QWidget)
Oyun tahtası grafiği.

**Önemli Metotlar:**
- `pos_to_coords(position)`: Pozisyon → pixel koordinat
- `paintEvent()`: Tahtayı çizer
- `update_positions()`: Piyonları günceller

**Renk Şeması:**
- Player 1: Kırmızı (#FF0000)
- Player 2: Mavi (#0000FF)

##### 3. `GameClient`
Socket iletişimi.

**Bağlantı Akışı:**
```
connect_to_server()
    ├─ Socket oluştur
    ├─ Sunucuya bağlan
    └─ receive_messages() thread'ini başlat
        └─ Sonsuz döngüde mesaj dinle
```

**JSON Mesaj Formatı:**
```python
# Gönder
{"type": "roll_dice"}

# Al
{"type": "dice_rolled", "player_id": 1, "dice_value": 4, ...}
```

##### 4. `ConnectionDialog` (QDialog)
Sunucu bağlantısı diyaloğu.

##### 5. `GameWindow` (QMainWindow)
Ana pencere ve UI yönetimi.

**Sinyal Bağlantıları:**
```python
message_received → on_message_received()
connection_failed → on_connection_failed()
connection_established → on_connection_established()
disconnected → on_disconnected()
```

---

## 🔄 Oyun Akışı

```
1. İstemci Başlat
   ├─ ConnectionDialog göster
   └─ Sunucuya bağlan

2. Bağlantı Kuruldu
   ├─ player_id al
   └─ UI'yi aktifleştir

3. Oyun Başladı
   ├─ board_state al
   └─ "Zar At" butonunu aktif et (Oyuncu 1 için)

4. Oyuncu Zar Atar
   ├─ "Zar At" butonuna tıkla
   └─ "roll_dice" mesajı gönder

5. Sunucu İşleme Alır
   ├─ Zar at
   ├─ Oyuncuyu taşı
   ├─ Merdiven/Yılan kontrol et
   ├─ board_state güncelle
   └─ Tüm istemcilere gönder

6. İstemci Güncelle
   ├─ board_updated mesajı al
   ├─ Tahtayı çiz
   ├─ Oyuncu sırasını değişken
   └─ "Zar At" butonunu kontrol et

7. Tekrar 4-6 (Kazanan olana kadar)

8. Oyun Bitti
   ├─ Winner mesajı al
   ├─ "Oyunu Sıfırla" butonunu aktif et
   └─ Bekle

9. Oyunu Sıfırla
   ├─ "Oyunu Sıfırla" butonuna tıkla
   └─ "reset_game" mesajı gönder
   └─ Adım 3'e dön
```

---

## 🔧 Uzantılar ve İyileştirmeler

### 1. Veritabanı Entegrasyonu

```python
# server.py'ye ekle
import sqlite3

class GameDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('games.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                name TEXT,
                wins INTEGER,
                losses INTEGER
            )
        ''')
        self.conn.commit()
```

### 2. Çok Oyunlu Oyun Desteği

```python
# Birden fazla oyun odasını destekle
class GameRoom:
    def __init__(self, room_id, max_players=2):
        self.room_id = room_id
        self.players = {}
        self.game = SnakesAndLaddersGame()
        self.max_players = max_players
    
    def add_player(self, player_id, socket):
        if len(self.players) < self.max_players:
            self.players[player_id] = socket
            return True
        return False
```

### 3. Oyuncu Sıralamalar

```python
class PlayerRanking:
    def __init__(self):
        self.rankings = {}
    
    def add_win(self, player_name):
        if player_name not in self.rankings:
            self.rankings[player_name] = {"wins": 0, "losses": 0}
        self.rankings[player_name]["wins"] += 1
    
    def get_top_10(self):
        return sorted(
            self.rankings.items(),
            key=lambda x: x[1]["wins"],
            reverse=True
        )[:10]
```

### 4. Ses Efektleri (PyQt5)

```python
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

class GameAudio:
    def __init__(self):
        self.player = QMediaPlayer()
    
    def play_dice_sound(self):
        self.player.setMedia(QMediaContent(QUrl("sounds/dice.wav")))
        self.player.play()
    
    def play_winner_sound(self):
        self.player.setMedia(QMediaContent(QUrl("sounds/winner.wav")))
        self.player.play()
```

### 5. Web API (Flask)

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/games', methods=['GET'])
def get_games():
    return jsonify({"active_games": get_active_games()})

@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    return jsonify(get_top_players())
```

---

## 🧪 Test Etme

### Unit Test Örneği

```python
import unittest

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        self.game = SnakesAndLaddersGame()
    
    def test_dice_roll(self):
        dice = self.game.roll_dice()
        self.assertGreaterEqual(dice, 1)
        self.assertLessEqual(dice, 6)
    
    def test_ladder(self):
        result = self.game.move_player(1, 1)  # Pozisyon 1
        self.assertEqual(result['current_position'], 38)  # Merdiven kontrol
    
    def test_snake(self):
        result = self.game.move_player(1, 17)  # Pozisyon 17
        self.assertEqual(result['current_position'], 7)  # Yılan kontrol
    
    def test_winner(self):
        result = self.game.move_player(1, 100)
        self.assertTrue(result['is_winner'])
```

### Entegrasyon Test

```bash
# Terminal 1
python server.py

# Terminal 2
python test_connection.py localhost 5000

# Terminal 3 & 4
python client.py
```

---

## 📊 Performans Notları

1. **Thread Güvenliği**: `threading.Lock()` kullanılarak veri tutarlılığı sağlanır
2. **Bağlantı Zaman Aşımı**: 5 saniye timeout ile bağlantı sağlanır
3. **JSON Buffer**: Her mesaj `\n` ile sonlandırılır (Boundary bildirimi)
4. **Broadcast**: Tüm istemcilere tek tek gönderilir (Optimize edilebilir)

---

## 🐛 Debugging Tavsiyeleri

### Logging Seviyeleri

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Detaylı bilgi")
logger.info("Genel bilgi")
logger.warning("Uyarı")
logger.error("Hata")
```

### Breakpoint'ler (VSCode)

```python
# server.py'de
def handle_client(self, client_socket):
    breakpoint()  # VSCode debugger'ı burada durur
    # Kodu debug et
```

---

## 📝 Kodlama Standartları

1. **Docstring Formatı**:
```python
def method_name(param1: str, param2: int) -> bool:
    """
    Kısa açıklama.
    
    Args:
        param1: Parametrenin açıklaması
        param2: Başka bir parametrenin açıklaması
    
    Returns:
        Dönüş değerinin açıklaması
    """
    pass
```

2. **Type Hints**: Tüm fonksiyonlarda type hints kullan
3. **Hata İşleme**: Her socket işleminde try-except kullan
4. **UTF-8**: Türkçe karakterler için `# -*- coding: utf-8 -*-` ekle

---

## 🚀 Deployment Checklist

- [ ] Tüm `print()` debug ifadeleri kaldırıldı mı?
- [ ] Logging konfigürasyonu production'a ayarlandı mı?
- [ ] Hardcoded IP/Port'lar kaldırıldı mı?
- [ ] Error handling kapsamlı mı?
- [ ] UTF-8 encoding ayarları doğru mu?
- [ ] Security groups ayarlandı mı (AWS)?
- [ ] Firewall kuralları ayarlandı mı?

---

Sorularınız varsa kod yorumlarını kontrol edin! 📖
