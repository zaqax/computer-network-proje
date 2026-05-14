

echo "========================================="
echo "Snakes & Ladders - AWS EC2 Kurulumu"
echo "========================================="

# Sistem güncellemeleri
echo "📦 Sistem paketleri güncelleniyor..."
sudo apt update
sudo apt upgrade -y

# Python ve pip kurulumu
echo "🐍 Python 3 ve pip kurulması..."
sudo apt install -y python3 python3-pip

# Proje dizinine git
cd ~/SnakesAndLadders || mkdir -p ~/SnakesAndLadders && cd ~/SnakesAndLadders

# Bağımlılıkları kur
echo "📚 Bağımlılıklar kurulıyor..."
pip3 install -r requirements.txt

# Sunucuyu systemd service olarak kaydet (opsiyonel)
echo "🚀 Sunucu servisini oluşturuyor..."

sudo tee /etc/systemd/system/snakes-ladders.service > /dev/null <<EOF
[Unit]
Description=Snakes and Ladders Game Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/SnakesAndLadders
ExecStart=/usr/bin/python3 $HOME/SnakesAndLadders/server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Servis başlatma (opsiyonel)
echo "✅ Kurulum tamamlandı!"
echo ""
echo "📝 Sunucuyu başlatmak için:"
echo "   # Direkt çalıştırmak:"
echo "   python3 server.py"
echo ""
echo "   # Ya da systemd service olarak:"
echo "   sudo systemctl start snakes-ladders"
echo "   sudo systemctl enable snakes-ladders"
echo ""
echo "🌐 Sunucunun Public IP adresini bul:"
echo "   curl https://checkip.amazonaws.com"
echo ""
echo "💡 İstemcileri lokal bilgisayardan bağlamak için:"
echo "   1. Python client.py çalıştır"
echo "   2. IP adresine EC2 Public IP'yi gir"
echo "   3. Port: 5000"
