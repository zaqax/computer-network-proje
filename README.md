# Yılanlar ve Merdivenler - Ağ Üzerinden Oyun

Python 3 ve Qt (PyQt5) kullanarak geliştirilmiş, TCP soketleri üzerinden iki oyuncuyla oynanan Snakes and Ladders oyunu.

## 📋 Özellikler

- **Sunucu-İstemci Mimarisi**: TCP soketleri ile ağ üzerinden iletişim
- **Grafik Arayüz**: PyQt5 ile oluşturulan modern GUI
- **JSON İletişimi**: Standar JSON formatında sunucu-istemci haberleşmesi
- **Modüler Kod Yapısı**: Temiz ve bakımlanabilir kod
- **Türkçe Karakter Desteği**: UTF-8 kodlama ile tam Türkçe destek
- **Hata Yönetimi**: Kapsamlı exception handling ve logging
- **10x10 Oyun Tahtası**: Klasik Snakes and Ladders kurallarına uygun
- **Merdiven ve Yılanlar**: Tanımlanmış konumlarda otomatik hareket

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Sunucusu                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ server.py - GameServer                           │   │
│  │ ├─ TCP Server (Port 5000)                       │   │
│  │ ├─ SnakesAndLaddersGame (Oyun Mantığı)         │   │
│  │ └─ JSON Mesaj İşleme                           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
          ↑                          ↑
     TCP Socket                 TCP Socket
          ↓                          ↓
┌──────────────────────┐  ┌──────────────────────┐
│  İstemci 1           │  │  İstemci 2           │
│ (client.py - GUI)    │  │ (client.py - GUI)    │
│ ├─ PyQt5 GUI         │  │ ├─ PyQt5 GUI         │
│ ├─ Oyun Tahtası      │  │ ├─ Oyun Tahtası      │
│ └─ Socket İstemcisi  │  │ └─ Socket İstemcisi  │
└──────────────────────┘  └──────────────────────┘
```

## 📦 Kurulum

### Gereksinimler
- Python 3.7 veya daha yüksek
- pip paket yöneticisi
- Windows, macOS veya Linux

### Adım 1: Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### Adım 2: Uygulamaları Çalıştır

#### Sunucuyu Başlat (AWS veya Lokal)
```bash
python server.py
```

Çıktı:
```
2026-05-11 10:00:00,123 - INFO - Sunucu başlatıldı: 0.0.0.0:5000
2026-05-11 10:00:00,124 - INFO - İstemcileri bekliyorum...
```

#### İstemci Uygulamasını Başlat (2 ayrı terminal)
```bash
python client.py
```

Her istemci açıldığında:
1. Bağlantı diyaloğu görüntülenir
2. Sunucu IP adresini girin (lokal: `127.0.0.1`, AWS: sunucu IP'si)
3. Port girin (varsayılan: `5000`)
4. "Bağlan" butonuna tıklayın

## 🎮 Oynanış Talimatları

1. **Sunucuyu Başlat**: İlk olarak sunucuyu çalıştırın
2. **İstemcileri Bağla**: İki ayrı istemciyi başlatın ve sunucuya bağlayın
3. **Oyunu Başlat**: Her iki oyuncu bağlandığında oyun otomatik başlar
4. **Zar Atın**: Sıranız geldiğinde "Zar At" butonuna tıklayın
5. **Haritada İzleyin**: Piyonlar haritada otomatik hareket eder
   - **Kırmızı piyon**: Oyuncu 1
   - **Mavi piyon**: Oyuncu 2
6. **100'e Ulaşın**: İlk 100 numarasına ulaşan oyuncu kazanır
7. **Yeniden Oyna**: Oyun bittikten sonra "Oyunu Sıfırla" butonuna tıklayın

## 📝 İletişim Protokolü (JSON)

### İstemci → Sunucu

#### Zar At İsteği
```json
{
  "type": "roll_dice"
}
```

#### Tahtanın Durumunu İste
```json
{
  "type": "request_board_state"
}
```

#### Oyunu Sıfırla
```json
{
  "type": "reset_game"
}
```

### Sunucu → İstemci

#### Oyuncu Atandı
```json
{
  "type": "player_assigned",
  "player_id": 1,
  "message": "Oyuncu 1 olarak oyuna katıldınız"
}
```

#### Oyun Başladı
```json
{
  "type": "game_started",
  "message": "Oyun başladı! Oyuncu 1 zar atabilir.",
  "board_state": {
    "player1_position": 0,
    "player2_position": 0,
    "current_player": 1,
    "game_state": "in_progress",
    "winner": null
  }
}
```

#### Zar Atıldı (Yanıt)
```json
{
  "type": "dice_rolled",
  "player_id": 1,
  "dice_value": 4,
  "move_result": {
    "success": true,
    "message": "Konumunuz: 4",
    "current_position": 4,
    "is_winner": false,
    "player_id": 1
  }
}
```

#### Tahtanın Durumu Güncellendi
```json
{
  "type": "board_updated",
  "board_state": {
    "player1_position": 4,
    "player2_position": 0,
    "current_player": 2,
    "game_state": "in_progress",
    "winner": null
  }
}
```

#### Hata
```json
{
  "type": "error",
  "message": "Sıra Oyuncu 2'de"
}
```

## 🎯 Oyun Kuralları

### Merdivenler (Peki Yin olağını!!!)
- 1 → 38 (Bir merdivene çıkıyorsunuz!)
- 4 → 14
- 9 → 31
- 21 → 42
- 28 → 84
- 51 → 67
- 72 → 91
- 80 → 99

### Yılanlar (Dikkat!)
- 17 → 7 (Bir yılanla karşılaştınız!)
- 54 → 34
- 62 → 18
- 88 → 24
- 95 → 75
- 97 → 79

### Oyun Mantığı
1. Oyuncu sırasıyla zar atar (1-6 arası rastgele sayı)
2. Piyon zar sayısı kadar ilerler
3. Merdivene çıkılırsa piyon merdivenin sonuna gider
4. Yılanla karşılaşılırsa piyon yılanın sonuna gider
5. Zar sonucu 100'ü geçerse, piyon hareket etmez
6. İlk 100'e ulaşan oyuncu oyunu kazanır

## 🛠️ Dosya Yapısı

```
SnakesAndLadders/
├── server.py              # Sunucu uygulaması (CLI)
├── client.py              # İstemci uygulaması (PyQt5 GUI)
├── requirements.txt       # Python bağımlılıkları
└── README.md              # Bu dosya
```

## 📚 Kod Mimarisi

### server.py
- **SnakesAndLaddersGame**: Oyun mantığı sınıfı
  - `roll_dice()`: Zar atmak
  - `move_player()`: Oyuncuyu taşımak
  - `get_board_state()`: Tahta durumunu almak
  
- **GameServer**: Sunucu sınıfı
  - `accept_connections()`: İstemci bağlantılarını kabul etmek
  - `handle_client()`: İstemciyi işlemek
  - `process_message()`: Mesajları işlemek
  - `broadcast()`: Tüm istemcilere mesaj göndermek

### client.py
- **GameClient**: Socket yönetimi sınıfı
  - `connect_to_server()`: Sunucuya bağlanmak
  - `send_message()`: Mesaj göndermek
  - `receive_messages()`: Mesaj almak (thread'de)
  
- **GameBoardWidget**: Oyun tahtası görüntüsü (PyQt5)
  - `paintEvent()`: Tahtayı çizmek
  - `update_positions()`: Piyonları güncellemek
  
- **GameWindow**: Ana pencere (PyQt5)
  - `roll_dice()`: Zar atma işlemi
  - `on_message_received()`: Sunucudan gelen mesajları işlemek

## 🔐 Hata Yönetimi

- **Socket Hataları**: Bağlantı hatalarında kullanıcıya bildirim
- **JSON Hatası**: Malformed JSON verisi işlenir
- **Ağ Zaman Aşımı**: 5 saniye timeout ile bağlantı sağlanır
- **Thread Güvenliği**: `threading.Lock()` ile veri tutarlılığı

## 📡 AWS'de Dağıtım

### EC2 Instance'ta Sunucuyu Çalıştırma

1. **SSH ile bağlan**:
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

2. **Python ve pip kur**:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

3. **Bağımlılıkları kur**:
```bash
pip3 install -r requirements.txt
```

4. **Sunucuyu çalıştır**:
```bash
python3 server.py
```

5. **Security Group ayarla** (AWS Console):
   - İnbound: TCP Port 5000 (0.0.0.0/0 veya belirtilen IP)

### İstemcileri Çalıştırma

Lokal bilgisayarlardan:
1. EC2 örneğinin public IP'sini alın
2. İstemciyi çalıştırın: `python client.py`
3. Bağlantı diyalogunda EC2 IP'sini girin

## 🐛 Sorun Giderme

### Bağlantı Hatası
- Sunucunun çalışıp çalışmadığını kontrol edin
- Firewall ayarlarını kontrol edin
- IP adresinin doğru olduğunu doğrulayın

### GUI Görüntülenmiyor
- PyQt5'in yüklü olduğunu kontrol edin: `pip show PyQt5`
- Eksikse: `pip install PyQt5`

### UTF-8 Karakterleri Görüntülenmiyor
- Python dosyalarının `# -*- coding: utf-8 -*-` bildirimi olduğundan emin olun
- JSON'da `ensure_ascii=False` kullanıldığından emin olun

### Sunucu 2 oyuncudan daha fazla bağlantı alıyor
- Sunucu tasarımı 2 oyuncu ile sınırlıdır
- Başka oyuncuların bağlanması otomatik olarak reddet

## 📄 Lisans

Bu proje eğitim amaçlı oluşturulmuştur.

## 👨‍💻 Geliştirici Notları

### İleri Geliştirmeler
- Veritabanı ile oyuncu geçmişi tutmak
- Birden fazla oyun odasını desteklemek
- Oyuncu reytingleri ve sıralamalar
- Sesli ve görsel efektler
- Web API ile entegrasyon

### Kodun Temel Özellikleri
✅ Modüler mimarisi  
✅ Exception handling  
✅ UTF-8 desteği  
✅ Thread güvenliği  
✅ JSON iletişimi  
✅ Kapsamlı logging  
✅ GUI tasarımı  
✅ Ağ üzerinden oyun  

---

**Oyunu Keyfini Çıkarın!** 🎲🐍🪜
