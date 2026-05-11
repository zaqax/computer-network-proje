# Snakes and Ladders Game - Hızlı Başlangıç Kılavuzu

## 🚀 5 Dakikada Başlayın

### Lokal Bilgisayarda Test Etme

#### 1. Ortamı Hazırla
```bash
cd d:\Documents\SnakesAndLadders
pip install -r requirements.txt
```

#### 2. Terminal 1: Sunucuyu Başlat
```bash
python server.py
```

Bekle şu mesajı görebilene kadar:
```
INFO - Sunucu başlatıldı: 0.0.0.0:5000
INFO - İstemcileri bekliyorum...
```

#### 3. Terminal 2: İstemci 1'i Başlat
```bash
python client.py
```

Bağlantı diyalogunda:
- IP: `127.0.0.1`
- Port: `5000`
- Bağlan'a tıkla

#### 4. Terminal 3: İstemci 2'yi Başlat
```bash
python client.py
```

Aynı ayarlarla bağlan.

**Oyun otomatik başlayacak!** Zar At butonuna tıkla ve eğlen.

---

## ☁️ AWS'de Dağıtma

### Adım 1: EC2 Instance Oluştur

1. AWS Console → EC2 → Instances → Launch Instance
2. **AMI Seç**: Ubuntu 22.04 LTS (Free Tier uygun)
3. **Instance Type**: t2.micro (Free Tier)
4. **Security Group** (Yeni Oluştur):
   - Inbound Rule: TCP 5000 from 0.0.0.0/0
5. **Key Pair**: Yeni oluştur ve indir (örn: `snakes-key.pem`)
6. Launch

### Adım 2: Dosyaları EC2'ye Aktar

```bash
# Lokal bilgisayardan
scp -i snakes-key.pem -r SnakesAndLadders ubuntu@EC2_PUBLIC_IP:~/
```

### Adım 3: EC2'de Sunucuyu Çalıştır

```bash
# EC2'ye SSH ile bağlan
ssh -i snakes-key.pem ubuntu@EC2_PUBLIC_IP

# Ubuntu'da
cd SnakesAndLadders
sudo apt update
sudo apt install -y python3 python3-pip python3-pyqt5

# PyQt5 kur (server'da isteğe bağlı, ama işleri basit tutmak için)
pip3 install PyQt5

# Sunucuyu çalıştır
python3 server.py
```

### Adım 4: Lokal İstemcileri Bağla

EC2 örneğinin Public IP'sini kopyala (örn: `54.123.45.67`)

```bash
python client.py
```

Bağlantı diyalogunda:
- IP: `EC2_PUBLIC_IP` (örn: `54.123.45.67`)
- Port: `5000`
- Bağlan

İkinci istemciyi de aynı IP ile bağla.

---

## 💻 Sistem Gereksinimleri

| Bileşen | Gereksinim |
|---------|-----------|
| Python | 3.7+ |
| PyQt5 | 5.15+ |
| İşletim Sistemi | Windows, macOS, Linux |
| Ağ | TCP Port 5000 |

## 🔧 Yapılandırma

### Sunucu Yapılandırması

`server.py` içinde değiştirilebilir ayarlar:

```python
# Port değişdir (satır ~285)
server = GameServer(host='0.0.0.0', port=5000)

# LADDERS ve SNAKES sözlüğünü düzenle (satır ~35-41)
LADDERS = {
    1: 38, 4: 14, ...
}
```

### İstemci Yapılandırması

`client.py` içinde varsayılan IP (satır ~200):

```python
self.ip_input.setText("127.0.0.1")  # Bunu değiştir
```

## 🎮 Kontrol Tuşları

| Eylem | Tuş/Buton |
|-------|-----------|
| Zar At | "Zar At" Butonu |
| Oyunu Sıfırla | "Oyunu Sıfırla" Butonu |
| Pencereyi Kapat | Alt+F4 (Windows) / Cmd+Q (Mac) |

## 📊 Oyun Durumları

```
WAITING_FOR_PLAYERS (Oyuncuları Bekleme)
        ↓
   (2 oyuncu bağlandı)
        ↓
IN_PROGRESS (Oyun Devam Ediyor)
        ↓
   (Birisinin puanı 100'e ulaştı)
        ↓
FINISHED (Oyun Bitti)
        ↓
   ("Oyunu Sıfırla" butonuna basıldı)
        ↓
IN_PROGRESS (Yeniden Oyun Devam)
```

## 📋 Sorun Giderme Kontrol Listesi

- [ ] Python kurulu mu? (`python --version`)
- [ ] PyQt5 kurulu mu? (`pip show PyQt5`)
- [ ] Port 5000 açık mı? (Firewall kontrol)
- [ ] Sunucu çalışıyor mu?
- [ ] İstemciler sunucunun adresine bağlantı yapabiliyor mu?
- [ ] Antivirus port 5000'i bloklayan bir şey yapmıyor mu?

## 🚀 Performans İpuçları

1. **Sunucuyu Yüksek Performanslı Makinaya Koy**
2. **İstemcilerin Aynı Ağda Olması Hızlı Bağlantı Sağlar**
3. **AWS'de Sunucu Kurarken Latency'i Düşür**

## 📞 Destek

Sorun yaşanırsa:
1. Terminal çıktılarını kontrol et (hata mesajları)
2. README.md'deki "Sorun Giderme" bölümünü oku
3. Kod yorumlarını kontrol et
4. Logging çıktısını kontrol et

---

**Başarılar!** 🎲
