import streamlit as st
import qrcode
import qrcode.image.svg
import io
import base64

st.set_page_config(page_title="QR Generator PRO", layout="centered")

st.title("📐 Generatore QR Vettoriale Centrato")

# --- CONFIGURAZIONE ---
formati_mm = {
    "Etichetta Piccola (50x30mm)": (50, 30),
    "Etichetta Media (100x50mm)": (100, 50),
    "A6": (105, 148),
    "A5": (148, 210),
    "A4": (210, 297),
}

st.sidebar.header("Impostazioni Pagina")
scelta = st.sidebar.selectbox("Dimensione Foglio:", list(formati_mm.keys()))
orientamento = st.sidebar.radio("Orientamento:", ["Verticale", "Orizzontale"])

# --- INPUT ---
col1, col2 = st.columns(2)
with col1:
    data = st.text_input("Dati QR (URL/ID):", "https://google.com")
with col2:
    label = st.text_input("Testo sotto (Etichetta):", "CONTROLLO QUALITÀ")

def generate_qr_svg():
    # 1. Dimensioni foglio
    w_mm, h_mm = formati_mm[scelta]
    width, height = (max(w_mm, h_mm), min(w_mm, h_mm)) if orientamento == "Orizzontale" else (min(w_mm, h_mm), max(w_mm, h_mm))

    # Margini (10%)
    margin = width * 0.1
    safe_w = width - (margin * 2)
    safe_h = height - (margin * 2)

    # 2. Generazione QR (border=0 per gestire noi i margini esattamente)
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(box_size=10, border=0) 
    qr.add_data(data)
    qr.make(fit=True)
    img_svg = qr.make_image(image_factory=factory)
    
    # Estrazione percorso
    svg_str = img_svg.to_string().decode('utf-8')
    start = svg_str.find('<path')
    end = svg_str.rfind('/>') + 2
    path_content = svg_str[start:end]
    
    # 3. Calcolo Dimensioni e Centratura
    # Il QR deve essere un quadrato, basato sulla dimensione minima disponibile
    code_size = min(safe_w, safe_h * 0.75)
    
    # Calcolo fattore di scala basato sulla dimensione reale dei moduli del QR
    # img_svg.width è il numero di moduli (es. 21, 25, etc.)
    scale_factor = code_size / img_svg.width
    
    # Centratura X matematica perfetta
    offset_x = (width - code_size) / 2
    
    # Gestione Testo
    font_size = code_size * 0.12
    caratteri = len(label) if len(label) > 0 else 1
    larghezza_stimata_testo = font_size * 0.6 * caratteri
    
    if larghezza_stimata_testo > code_size:
        font_size = font_size * (code_size / larghezza_stimata_testo)

    # Centratura verticale del blocco
    spazio_testo = font_size * 1.5
    altezza_blocco = code_size + spazio_testo
    offset_y = (height - altezza_blocco) / 2

    # 4. Assemblaggio
    svg_full = f"""
    <svg width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="white"/>
        <g transform="translate({offset_x}, {offset_y}) scale({scale_factor})">
            {path_content}
        </g>
        <text x="{width/2}" y="{offset_y + code_size + (font_size * 0.8)}" 
            font-family="Arial, sans-serif" 
            font-size="{font_size}" 
            text-anchor="middle" 
            dominant-baseline="hanging"
            fill="black">{label}</text>
    </svg>
    """
    return svg_full

if data:
    try:
        final_svg = generate_qr_svg()
        b64 = base64.b64encode(final_svg.encode('utf-8')).decode("utf-8")
        st.write(f'<div style="text-align:center; background:#f9f9f9; padding:20px; border-radius:10px;"><img src="data:image/svg+xml;base64,{b64}" style="width:100%; max-width:{formati_mm[scelta][0]*4}px;"/></div>', unsafe_allow_html=True)
        
        st.download_button("💾 Scarica SVG Centrato", final_svg, "qr_perfetto.svg", "image/svg+xml")
    except Exception as e:
        st.error(f"Errore: {e}")
