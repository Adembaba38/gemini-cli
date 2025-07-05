# 🚀 Effinova Panel - Kullanım Kılavuzu

## 📋 Genel Bakış

**Effinova Panel**, çalışan yönetimi, süreç takibi, inovasyon yönetimi ve performans analizi için geliştirilmiş kapsamlı bir web uygulamasıdır.

## ✅ Sorun Çözüldü!

Daha önce karşılaşılan sorunlar başarıyla çözüldü:
- ✅ **Streamlit eksikliği** - Sanal ortam oluşturuldu ve tüm paketler yüklendi
- ✅ **Modül importları** - config.py, excel_to_db.py, employees.py modülleri hazırlandı
- ✅ **Veritabanı bağlantısı** - SQLite veritabanı başarıyla çalışıyor
- ✅ **Kod organizasyonu** - Ana kod temizlendi, modüler yapı oluşturuldu

## 🛠️ Kurulum ve Başlatma

### 1. Hızlı Başlatma
```bash
# Basit başlatma scripti ile
./run_app.sh
```

### 2. Manuel Başlatma
```bash
# Sanal ortamı aktifleştir
source effinova_env/bin/activate

# Uygulamayı başlat
streamlit run effinova_panel.py --server.port=8501 --server.address=0.0.0.0
```

### 3. Uygulamaya Erişim
- **Yerel:** `http://localhost:8501`
- **Ağ:** `http://[IP_ADRESINIZ]:8501`

## 📊 Uygulama Özellikleri

### 🏠 Ana Sekmeler
1. **Çalışan Yönetimi** - Personel kayıtları ve bilgileri
2. **Canlı Süreç Yönetimi** - Aktif süreçlerin takibi
3. **İnovasyon** - Yenilikçi fikirlerin yönetimi
4. **Proje Yönetimi** - Proje takibi ve koordinasyonu
5. **Raporlar** - Detaylı analiz ve raporlama
6. **Kullanıcı Yönetimi** - Sistem kullanıcı yönetimi
7. **Rozetler** - Başarı ve ödül sistemi
8. **Lider Tablosu** - Performans sıralamaları
9. **Performans Paneli** - Anlık performans göstergeleri
10. **Sistem Onarım & Loglar** - Sistem bakım araçları
11. **Analitik** - Veri analizi ve görselleştirme
12. **Excel İçe Aktarım** - Toplu veri yükleme

### 🔧 Teknik Özellikler
- **Veritabanı:** SQLite (varsayılan) / MySQL (opsiyonel)
- **Web Framework:** Streamlit
- **Veri Analizi:** Pandas, NumPy
- **Görselleştirme:** Plotly
- **Önbellekleme:** Streamlit cache sistemi
- **Logging:** Kapsamlı olay kayıtları

## 📁 Dosya Yapısı

```
/workspace/
├── effinova_panel.py      # Ana uygulama dosyası
├── config.py              # Veritabanı ve konfigürasyon
├── excel_to_db.py         # Excel import fonksiyonları
├── employees.py           # Çalışan yönetimi modülü
├── effinova_env/          # Python sanal ortamı
├── run_app.sh             # Başlatma scripti
├── test_config.py         # Veritabanı test dosyası
└── NASIL_KULLANILIR.md    # Bu kılavuz
```

## 🔍 Test ve Doğrulama

### Veritabanı Testi
```bash
# Veritabanı bağlantısını test et
python test_config.py
```

### Modül Testi
```bash
# Sanal ortamda Python çalıştır
source effinova_env/bin/activate
python -c "import config; print('✅ Config OK')"
```

## 🚨 Sorun Giderme

### Yaygın Sorunlar ve Çözümleri

1. **Port 8501 kullanımda hatası:**
```bash
# Farklı port kullan
streamlit run effinova_panel.py --server.port=8502
```

2. **Paket eksikliği:**
```bash
# Sanal ortamı aktifleştir
source effinova_env/bin/activate
# Eksik paketi yükle
pip install [paket_adı]
```

3. **Veritabanı sorunu:**
```bash
# Test çalıştır
python test_config.py
```

## 🔧 Geliştirme

### Yeni Özellik Ekleme
1. `effinova_panel.py` dosyasını düzenle
2. Gerekirse yeni modüller oluştur
3. Uygulamayı yeniden başlat

### Veritabanı Değişiklikleri
- `config.py` dosyasında modelleri güncelle
- Migrasyon fonksiyonlarını çalıştır

## 📈 Performans İpuçları

- **Önbellekleme:** Streamlit cache dekoratörlerini kullan
- **Veri Yükleme:** Büyük veri setleri için chunk-based yükleme
- **Görselleştirme:** Plotly grafiklerini optimize et

## 📞 Destek

Herhangi bir sorunla karşılaştığınızda:
1. Önce `test_config.py` çalıştırın
2. Log dosyalarını kontrol edin
3. Hata mesajlarını kaydedin

## 🎉 Başarılı Kurulum!

✅ **Tüm bileşenler hazır**
✅ **Veritabanı çalışıyor**
✅ **Web arayüzü erişilebilir**
✅ **Modüller yüklendi**

**Artık Effinova Panel'i kullanmaya başlayabilirsiniz!** 🚀