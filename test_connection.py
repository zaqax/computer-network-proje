#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snakes and Ladders Game - Bağlantı Test Aracı
Sunucuya bağlanabilirliği test et
"""

import socket
import json
import sys
from typing import Tuple

def test_connection(host: str, port: int) -> bool:
    """Sunucuya bağlanmayı test et"""
    try:
        print(f"\n🔗 {host}:{port}'a bağlanılıyor...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        print("✅ Bağlantı başarılı!")
        
        # Sunucudan ilk mesajı al
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        
        if data:
            try:
                message = json.loads(data.decode("utf-8").strip())
                print(f"📨 Sunucu Mesajı: {message.get('message', 'Bilinmeyen mesaj')}")
            except:
                print(f"📨 Ham Veri: {data}")
        
        sock.close()
        return True
    
    except socket.timeout:
        print("❌ Hata: Sunucuya bağlantı zaman aşımına uğradı (5 saniye)")
        return False
    
    except ConnectionRefusedError:
        print("❌ Hata: Sunucu bağlantısını reddetti")
        print("   - Sunucunun çalışıp çalışmadığını kontrol edin")
        print("   - Doğru port kullandığınızı kontrol edin")
        return False
    
    except socket.gaierror:
        print("❌ Hata: Host adı çözümlenemedi")
        print("   - IP adresinin doğru olduğunu kontrol edin")
        return False
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False


def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("Snakes and Ladders - Bağlantı Test Aracı")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = input("\n🎯 Sunucu IP adresi (varsayılan: 127.0.0.1): ").strip() or "127.0.0.1"
    
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("❌ Hata: Port sayısal değer olmalıdır")
            return
    else:
        port_str = input("🎯 Port (varsayılan: 5000): ").strip() or "5000"
        try:
            port = int(port_str)
        except ValueError:
            print("❌ Hata: Port sayısal değer olmalıdır")
            return
    
    # Bağlantı testi
    if test_connection(host, port):
        print("\n✨ Sunucuya başarıyla bağlanabilirsiniz!")
        print("   İstemci uygulamasını çalıştırabilirsiniz:\n")
        print(f"   python client.py")
        print(f"\n   Bağlantı diyalogunda şunları girin:")
        print(f"   - IP: {host}")
        print(f"   - Port: {port}")
    else:
        print("\n⚠️  Sunucuya bağlanılamadı. Aşağıdakileri kontrol edin:")
        print("   1. Sunucunun çalışıp çalışmadığını kontrol edin")
        print("   2. IP adresi ve port'un doğru olduğunu kontrol edin")
        print("   3. Firewall'ın port 5000'i engellemeyen kontrol edin")
        print("   4. AWS'de Security Group ayarlarını kontrol edin")


if __name__ == "__main__":
    main()
