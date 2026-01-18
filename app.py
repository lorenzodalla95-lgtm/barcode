import streamlit as st
import qrcode
import qrcode.image.svg
import io
import base64
from fpdf import FPDF

st.set_page_config(page_title="QR PRO: Vettoriale & PDF", layout="centered")

st.title("📐 QR PRO: Generatore Professionale")
st.write("Crea QR code nitidi con testo proporzionato, pronti per la stampa.")

# --- CONFIGURAZIONE DIMENSIONI (mm) ---
formati_mm = {
    "Etichetta Piccola (50x30mm)": (50, 30),
    "Etichetta Media (100x50mm)": (100, 50),
    "A6 (Cartolina)": (105, 148),
    "A5": (148, 210),
    "A4": (210, 297),
}

# --- SIDEBAR ---
st.sidebar.header("Impostazioni Pagina")
scelta = st.sidebar.selectbox("Dimensione Foglio:", list(formati_mm.keys()))
orientamento = st.sidebar.radio("Orientamento:", ["Verticale", "Orizzontale"])
colore_anteprima = st.sidebar.color_picker("Colore Sfondo Anteprima", "#f0f2f6")

# --- INPUT DATI ---
col_in1, col_in2 = st.columns(2)
with col_in1:
    data_input = st.text_input("Dati nel QR (URL/ID):", "https://google.com")
with col_in2:
    label_text = st.text_input("Testo sotto (Etichetta):", "PRODOTTO ALPHA")

# --- LOGICA DI GENERAZIONE ---
def generate_assets():
    # 1. Calcolo dimensioni foglio
    w_base, h_base = formati_mm[scelta]
    w, h = (max(w_base, h_base), min(w_base, h_base)) if orientamento == "Orizzontale" else (min(w_base, h_base), max(w_base, h_base))

    # 2. Generazione QR Vettoriale (border=0 per centratura assoluta)
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(data_input)
    qr.make(fit=True)
    
    # SVG per anteprima e download
    factory = qrcode.image.svg.SvgPathImage
    img_svg = qr.make_image(image_factory=factory)
    svg_str = img_svg.to_string().decode('utf-8')
    path_start = svg_str.find('<path')
    path_end = svg_str.rfind('/>') + 2
    path_content = svg_str[path_start:path_end]

    # 3. Calcolo Proporzioni e Centratura
    margin = w * 0.1
    safe_w = w - (margin * 2)
    safe_h = h - (margin * 2)
    
    # Il QR occupa al max il 75% dell'altezza utile per far spazio al testo
    code_size = min(safe_w, safe_h * 0.75)
    scale_factor = code_size / img_svg.width
    
    # Testo adattivo: se troppo lungo, rimpicciolisce per non uscire dal QR
    font_size = code_size * 0.12
    caratteri = len(label_text) if len(label_text) > 0 else 1
    larghezza_stimata_testo = font_size * 0.55 * caratteri
    if larghezza_stimata_testo > code_size:
        font_size = font_size * (code_size / larghezza_stimata_testo)

    # Centratura verticale del blocco (QR + Testo)
    spazio_testo = font_size * 1.5
    altezza_blocco = code_size + spazio_testo
    ox = (w - code_size) / 2
    oy = (h - altezza_blocco) / 2
    
    # 4. Creazione SVG Finale
    svg_final = f"""
    <svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="white"/>
        <g transform="translate({ox}, {oy}) scale({scale_factor})">
            {path_content}
        </g>
        <text x="{w/2}" y="{oy + code_size + (font_size * 0.8)}" 
            font-family="Arial, sans-serif" font-size="{font_size}" 
            text-anchor="middle" dominant-baseline="hanging" fill="black">{label_text}</text>
    </svg>
    """

    # 5. Creazione PDF (Vettoriale)
    pdf = FPDF(orientation='L' if orientamento == "Orizzontale" else 'P', unit='mm', format=(w, h))
    pdf.add_page()
    
    # Per il PDF convertiamo temporaneamente il QR in PNG (alta risoluzione)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)
    
    pdf.image(buf, x=ox, y=oy, w=code_size, h=code_size)
    pdf.set_font("Arial", size=font_size)
    pdf.text(x=(w - pdf.get_string_width(label_text))/2, y=oy + code_size + (font_size * 1.1), txt=label_text)
    
    return svg_final, bytes(pdf.output()), w

# --- INTERFACCIA DI OUTPUT ---
if data_input:
    try:
        svg_out, pdf_out, width_mm = generate_assets()
        
        # TASTI DOWNLOAD (SOPRA)
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button("💾 Scarica SVG", svg_out, "codice.svg", "image/svg+xml", use_container_width=True)
        with col_dl2:
            st.download_button("📄 Scarica PDF", pdf_out, "codice.pdf", "application/pdf", use_container_width=True)

        st.divider()

        # ANTEPRIMA CON SFONDO PERSONALIZZATO
        b64 = base64.b64encode(svg_out.encode('utf-8')).decode("utf-8")
        st.write(
            f'''
            <div style="text-align:center; background:{colore_anteprima}; padding:40px; border-radius:15px; border:1px solid #ddd;">
                <img src="data:image/svg+xml;base64,{b64}" 
                     style="width:100%; max-width:{width_mm*4}px; box-shadow: 0 8px 20px rgba(0,0,0,0.2); border-radius:4px;"/>
            </div>
            ''', 
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"Errore tecnico: {e}")
