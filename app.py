import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="EFFINOVA Panel", layout="wide")

st.title("⭐ EFFINOVA Panel")
st.success("✅ Sistem çalışıyor!")

st.sidebar.title("🎯 Menü")
st.sidebar.info("👤 Admin")

# Basit form
with st.form("test_form"):
    name = st.text_input("Ad:")
    department = st.text_input("Departman:")
    
    if st.form_submit_button("Ekle"):
        if name:
            st.success(f"✅ {name} eklendi!")

st.info("🎉 Başarıyla çalışan minimal panel!")