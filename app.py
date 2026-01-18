import streamlit as st
import qrcode
import qrcode.image.svg
import io
import base64
from fpdf import FPDF

st.set_page_config(page_title="QR Generator PRO", layout="centered")

st.title("📐 QR PRO: SVG & PDF")

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
colore_anteprima = st.sidebar.color_picker("Sfondo Anteprima", "#f0f2f6")

# --- INPUT ---
col1, col2 = st.columns(2)
with col1:
    data = st.text_input("Dati QR (URL/ID):", "https://google.com")
with col2:
    label = st.text_input("Testo sotto (Etichetta):", "CONTROLLO QUALITÀ")

# --- LOGICA DI GENERAZIONE ---
def generate_qr_svg():
    w_mm, h_mm = formati_mm[scelta]
    width, height = (max(w_mm, h_mm), min(w_mm, h_mm)) if orientamento == "Orizzontale" else (min(w_mm, h_mm), max(w_mm, h_mm))

    margin = width * 0.1
    safe_w = width - (margin * 2)
    safe_h = height - (margin * 2)

    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(box_size=10, border=0) 
    qr.add_data(data)
    qr.make(fit=True)
    img_svg = qr.make_image(image_factory=factory)
    
    svg_str = img_svg.to_string().decode('utf-8')
    start = svg_str.find('<path')
    end = svg_str.rfind('/>') + 2
    path_content = svg_str[start:end]
    
    code_size = min(safe_w, safe_h * 0.75)
    scale_factor = code_size / img_svg.width
    offset_x = (width - code_size) / 2
    
    font_size = code_size * 0.12
    caratteri = len(label) if len(label) > 0 else 1
    larghezza_stimata_testo = font_size * 0.6 * caratteri
    if larghezza_stimata_testo > code_size:
        font_size = font_size * (code_size / larghezza_stimata_testo)

    spazio_testo = font_size * 1.5
    altezza_blocco = code_size + spazio_testo
    offset_y = (height - altezza_blocco) / 2

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
    return svg_full, width, height, offset_x, offset_y, code_size, font_size

def generate_pdf(w, h, data_qr, text_label, ox, oy, cs, fs):
    # Setup PDF con dimensioni personalizzate
    pdf = FPDF(orientation='L' if orientamento == "Orizzontale" else 'P', unit='mm', format=(w, h))
    pdf.add_page()
    
    # Generazione QR immagine per il PDF (fpdf non renderizza i path SVG complessi nativamente senza librerie extra pesanti)
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(data_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Salvataggio temporaneo in memoria
    img_buf = io.BytesIO()
    qr_img.save(img_buf, format='PNG')
    img_buf.seek(0)
    
    # Posizionamento elementi nel PDF
    pdf.image(img_buf, x=ox, y=oy, w=cs, h=cs)
    
    # Testo
    pdf.set_font("Arial", size=fs)
    # Calcoliamo la coordinata Y per il PDF (fpdf usa la baseline)
    pdf.text(x=(w/2) - (pdf.get_string_width(text_label)/2), y=oy + cs + (fs*0.8) + (fs/2), txt=text_label)
    
    return pdf.output()

# --- INTERFACCIA ---
if data:
    try:
        # Generiamo i dati comuni
        final_svg, w, h, ox, oy, cs, fs = generate_qr_svg()
        
        # 1. TASTI DI DOWNLOAD SOPRA
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button("💾 Scarica SVG (Vettoriale)", final_svg, "qr_vettoriale.svg", "image/svg+xml", use_container_width=True)
        with d_col2:
            pdf_bytes = generate_pdf(w, h, data, label, ox, oy, cs, fs)
            st.download_button("📄 Scarica PDF (Stampa)", pdf_bytes, "qr_stampa.pdf", "application/pdf", use_container_width=True)

        st.divider()

        # 2. BOX DI CREAZIONE (ANTEPRIMA)
        b64 = base64.b64encode(final_svg.encode('utf-8')).decode("utf-8")
        st.write(
            f'''
            <div style="
                text-align:center; 
                background:{colore_anteprima}; 
                padding:40px; 
                border-radius:15px;
                display: flex;
                justify-content: center;
                align-items: center;
            ">
                <img src="data:image/svg+xml;base64,{b64}" 
                     style="width:100%; max-width:{w*4}px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); border-radius: 4px;"/>
            </div>
            ''', 
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"Errore: {e}")
