#!/bin/bash

# Effinova Panel - Başlatma Scripti
# Bu script uygulamayı başlatmak için kullanılır

echo "🚀 Effinova Panel başlatılıyor..."
echo "⚙️ Sanal ortam aktifleştiriliyor..."

# Sanal ortamı aktifleştir
source effinova_env/bin/activate

echo "✅ Sanal ortam aktif!"
echo "📊 Streamlit uygulaması başlatılıyor..."

# Streamlit uygulamasını başlat
streamlit run effinova_panel.py --server.port=8501 --server.address=0.0.0.0

echo "🎉 Uygulama başlatıldı!"
echo "🔗 Tarayıcıdan şu adresi ziyaret edin: http://localhost:8501"