import streamlit as st
import qrcode
import qrcode.image.svg
from barcode import Code128
from barcode.writer import SVGWriter
import io
import base64
import xml.etree.ElementTree as ET

st.set_page_config(page_title="QR & Barcode Pro", layout="centered")

st.title("📐 Generatore Vettoriale Professionale")

# --- CONFIGURAZIONE ---
formati_mm = {
    "Etichetta Piccola (50x30mm)": (50, 30),
    "Etichetta Media (100x50mm)": (100, 50),
    "A6": (105, 148),
    "A5": (148, 210),
    "A4": (210, 297),
}

st.sidebar.header("Formato")
scelta = st.sidebar.selectbox("Dimensione:", list(formati_mm.keys()))
orientamento = st.sidebar.radio("Orientamento:", ["Verticale", "Orizzontale"])
tipo = st.sidebar.radio("Tipo:", ["QR Code", "Barcode 128"])

col1, col2 = st.columns(2)
with col1:
    data = st.text_input("Dati Codice:", "123456789")
with col2:
    label = st.text_input("Testo sotto (Etichetta):", "TESTO DI ESEMPIO MOLTO LUNGO")

def generate_svg():
    # 1. Calcolo dimensioni foglio
    w_mm, h_mm = formati_mm[scelta]
    width, height = (max(w_mm, h_mm), min(w_mm, h_mm)) if orientamento == "Orizzontale" else (min(w_mm, h_mm), max(w_mm, h_mm))

    margin = width * 0.1
    safe_w = width - (margin * 2)
    safe_h = height - (margin * 2)

    content_parts = ""
    
    if tipo == "QR Code":
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(data)
        qr.make(fit=True)
        img_svg = qr.make_image(image_factory=factory)
        
        # Estrazione path
        svg_str = img_svg.to_string().decode('utf-8')
        start = svg_str.find('<path')
        end = svg_str.rfind('/>') + 2
        path_content = svg_str[start:end]
        
        code_w = min(safe_w, safe_h * 0.7)
        code_h = code_w
        
        # Centratura QR
        scale = code_w / img_svg.width
        offset_x = (width - code_w) / 2
        offset_y = (height - (code_h * 1.3)) / 2 # Alziamo un po' per far spazio al testo
        
        content_parts = f'<g transform="translate({offset_x}, {offset_y}) scale({scale})">{path_content}</g>'
        
        # Logica Testo: larghezza testo = larghezza QR
        text_x = width / 2
        text_y = offset_y + code_h + (code_h * 0.15) # Spazio del 15% rispetto al QR
        font_size = code_w * 0.12 # Dimensione base proporzionata
        
    else:
        # Barcode 128
        rv = io.BytesIO()
        Code128(data, writer=SVGWriter()).write(rv, options={"write_text": False, "quiet_zone": 1})
        barcode_svg = rv.getvalue().decode('utf-8')
        
        # Estraiamo i rettangoli del barcode
        start = barcode_svg.find('<g id="barcode_group">')
        if start == -1: start = barcode_svg.find('<rect') # Fallback
        end = barcode_svg.rfind('</g>')
        if end == -1: end = barcode_svg.rfind('/>') + 2
        bar_content = barcode_svg[start:end]

        code_w = safe_w
        code_h = safe_h * 0.3
        
        scale_x = code_w / 500 # Valore approssimativo width interna barcode
        scale_y = code_h / 120
        
        offset_x = (width - code_w) / 2
        offset_y = (height - (code_h * 2)) / 2
        
        content_parts = f'<g transform="translate({offset_x}, {offset_y}) scale({scale_x}, {scale_y})">{bar_content}</g>'
        
        text_x = width / 2
        text_y = offset_y + code_h + (code_h * 0.5)
        font_size = code_w * 0.08

    # --- LOGICA ANTI-ESUBERO TESTO ---
    # Se il testo è troppo lungo rispetto alla larghezza del codice, lo scalo
    caratteri = len(label) if len(label) > 0 else 1
    larghezza_stimata_testo = font_size * 0.6 * caratteri
    
    if larghezza_stimata_testo > code_w:
        font_size = font_size * (code_w / larghezza_stimata_testo)

    # --- ASSEMBLAGGIO FINALE ---
    svg_full = f"""
    <svg width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="white"/>
        {content_parts}
        <text x="{text_x}" y="{text_y}" 
            font-family="Arial, Helvetica, sans-serif" 
            font-size="{font_size}" 
            text-anchor="middle" 
            dominant-baseline="middle"
            fill="black">{label}</text>
    </svg>
    """
    return svg_full

# --- INTERFACCIA ---
if data:
    try:
        final_svg = generate_svg()
        
        # Visualizzazione
        b64 = base64.b64encode(final_svg.encode('utf-8')).decode("utf-8")
        st.write(f'<div style="text-align:center; background:#eee; padding:20px; border-radius:10px;"><img src="data:image/svg+xml;base64,{b64}" style="max-width:100%; height:auto; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/></div>', unsafe_allow_html=True)

        st.divider()
        
        st.download_button(
            label="💾 Scarica SVG (Vettoriale per Stampa)",
            data=final_svg,
            file_name=f"codice_{scelta.replace(' ', '_')}.svg",
            mime="image/svg+xml"
        )
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
