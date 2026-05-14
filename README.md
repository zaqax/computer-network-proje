# Yılanlar ve Merdivenler Oyunu

Bu proje, minimum iki maksimum beş kullanıcının aynı oyunu ağ üzerinden eş zamanlı
şekilde oynayabilmesini sağlayan bir Yılanlar ve Merdivenler uygulamasıdır. Projede temel
amaç, client server yapısı kullanılarak gerçek zamanlı oyun akışını yönetmek ve kullanıcıya
GUI üzerinden akıcı bir deneyim sunmaktır. Uygulama Python programlama dili ile
geliştirilmiş olup ağ iletişimi için TCP soketleri kullanılmıştır. Grafik arayüz tarafında ise
PyQt5 tercih edilmiştir. Oyun yapısında oyuncu durumları, harita ve hamle kontrolü sözlük
tabanlı veri yapıları ile tutulmaktadır.

Sistem yapısı client ve server olmak üzere iki temel parçadan oluşmaktadır. Server tarafı
server.py, client tarafı ise client.py dosyaları üzerinden çalışmaktadır. Server uygulaması
oyunun genel durumunu yönetmekte ve bağlanan her oyuncu için ayrı bir thread oluşturarak
istemcilerden gelen mesajları işlemektedir. Client tarafında ise PyQt5 ile oluşturulmuş GUI
ve serverdan gelen mesajları dinleyen ayrı bir mesaj dinleme thread’i bulunmaktadır.

Oyunun çalışma mantığında istemci önce TCP bağlantısı üzerinden server’a bağlanır.
Server oyuncuya bir id ataması yapar ve güncel oyun haritasını tüm clientlara gönderir.
Sırası gelen oyuncu zar attığında hamle server tarafında hesaplanır ve sonuç tüm
oyunculara iletilir. Bir oyuncu oyunu kazandığında oyun sonlandırılır ve tüm clientlarda
kazanan veya kaybeden ekranı gösterilir. Oyuncuların tamamı devam butonuna bastığında
ise oyun sıfırlanarak yeniden başlatılır.

Client ve server arasındaki iletişim JSON formatındaki mesajlar ile sağlanmaktadır. Mesajlar
satır sonları ile ayrılarak tek bir TCP bağlantısı üzerinden gönderilmektedir. Sistem içerisinde
oyuncuya id atanması, bağlantının reddedilmesi, oyunun başlatılması, zar atılması, oyun
haritasının güncellenmesi, oyunun sona ermesi ve oyunun yeniden başlatılması gibi işlemler
için farklı mesajlar kullanılmaktadır. Ayrıca hata durumları için hata mesajları ve bağlantının
aktif olduğunu kontrol etmek amacıyla ping-pong mesajları bulunmaktadır. Server gelen tüm
mesajları yorumlamakta ve gerekli durumlarda tüm clientları uyarmaktadır. Eğer oyun aktif
durumda ise yeni bağlantılar reddedilmekte, oda kapasitesi doluysa yine bağlantı kabul
edilmemektedir.

GUI PyQt5 kullanılarak geliştirilmiştir. Arayüzde üst bölümde bağlantı ve sıra bilgilerini
gösteren bir durum alanı bulunmaktadır. Orta bölümde 10x10 boyutunda oyun haritası yer
almakta ve burada oyuncu taşları ile yılan ve merdiven ikonları gösterilmektedir. Alt bölümde
mesaj alanı ve oyuncu listesi bulunmaktadır. Ayrıca oyunun sonucuna göre kazanan veya
kaybeden ekranı ile bağlantı reddi ekranı gibi özel katmanlar da tasarlanmıştır. Tahtada
merdiven başlangıç noktalarında sol üstte, bitiş noktalarında ise sol altta ikonlar yer almakta;
yılan başlangıç noktaları da ikonlarla belirtilmektedir. Hücreler içerisinde başlangıç ve bitiş
bilgileri kullanıcıya gösterilmektedir.

Projenin test sürecinde farklı senaryolar manuel olarak denenmiştir. İki istemci ile oyunun
başlatılması ve oyuncuların sıralı şekilde zar atması test edilmiştir. Oyun devam ederken
yeni bir istemcinin bağlanma girişiminde bulunması durumunda bağlantının reddedildiği
doğrulanmıştır. Oda kapasitesi dolduğunda yeni bağlantıların engellenmesi de kontrol
edilmiştir. Ayrıca kazanan senaryoları test edilerek tüm istemcilerde doğru ekranların
görüntülendiği gözlemlenmiştir. Oyuncuların tamamının “Devam” butonuna basmasıyla
oyunun sıfırlanması ve yeniden başlaması başarılı şekilde çalışmıştır. Bunun yanında
oyunculardan birinin bağlantıyı kesmesi durumunda sunucunun oyun durumunu doğru
biçimde güncellediği görülmüştür.

Projeyi çalıştırmak için öncelikle gerekli bağımlılıkların pip install -r requirements.txt komutu
ile kurulması gerekmektedir. Daha sonra server tarafı python server.py komutu ile başlatılır.
Client uygulaması ise python client.py komutu ile çalıştırılır. Client açıldığında kullanıcıdan
server IP adresi ve port bilgisi istenir ve bağlantı bu bilgiler üzerinden sağlanır.

Sonuç olarak bu proje, TCP tabanlı client server mimarisi kullanılarak çok oyunculu ve eş
zamanlı bir oyun deneyimini başarılı şekilde sunmaktadır. Ağ iletişimi, gerçek zamanlı veri
aktarımı ve GUI entegrasyonu birlikte kullanılarak işlevsel bir sistem geliştirilmiştir.