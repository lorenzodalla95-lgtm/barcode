import streamlit as st
import qrcode
import qrcode.image.svg
from barcode import Code128
from barcode.writer import SVGWriter
import io
import base64

st.set_page_config(page_title="Vettoriale QR & Barcode", layout="centered")

st.title("📐 Generatore Vettoriale Nitido")
st.write("QR e Barcode in formato SVG (vettoriale) per la massima qualità di stampa.")

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
    label = st.text_input("Testo Etichetta:", "PRODOTTO ESEMPIO")

def get_svg():
    # Dimensioni in mm
    w_mm, h_mm = formati_mm[scelta]
    if orientamento == "Orizzontale":
        width, height = max(w_mm, h_mm), min(w_mm, h_mm)
    else:
        width, height = min(w_mm, h_mm), max(w_mm, h_mm)

    # Margine del 10%
    margin = min(width, height) * 0.1
    safe_w = width - (margin * 2)
    safe_h = height - (margin * 2)

    if tipo == "QR Code":
        # Generazione QR Vettoriale
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(data)
        qr.make(fit=True)
        img_svg = qr.make_image(image_factory=factory)
        
        # In un SVG, il QR è un percorso. Lo mettiamo in un contenitore centrato.
        code_size = min(safe_w, safe_h * 0.7) # Lasciamo spazio per il testo
        
        # Costruzione manuale dell'SVG per controllo totale
        svg_data = img_svg.to_string().decode('utf-8')
        # Estraiamo solo il contenuto del path per ricostruirlo
        content = svg_data.split('>', 1)[1].rsplit('<', 1)[0]
        
        # Calcolo posizioni
        text_size = code_size * 0.15 # Altezza testo proporzionale al codice
        total_content_h = code_size + (text_size * 1.2)
        
        start_y = (height - total_content_h) / 2
        
        svg_final = f"""
        <svg width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="white"/>
            <g transform="translate({(width-code_size)/2}, {start_y}) scale({code_size/img_svg.width})">
                {content}
            </g>
            <text x="{width/2}" y="{start_y + code_size + text_size}" 
                font-family="Arial, sans-serif" 
                font-size="{text_size}" 
                text-anchor="middle" 
                fill="black">{label}</text>
        </svg>
        """
    else:
        # Barcode 128 Vettoriale
        rv = io.BytesIO()
        Code128(data, writer=SVGWriter()).write(rv, options={
            "write_text": False,
            "margin_top": 0,
            "margin_bottom": 0,
            "quiet_zone": 1
        })
        svg_raw = rv.getvalue().decode('utf-8')
        content = svg_raw.split('>', 1)[1].rsplit('<', 1)[0]

        bar_w = safe_w
        bar_h = safe_h * 0.4
        text_size = bar_w * 0.08
        
        total_h = bar_h + text_size
        start_y = (height - total_h) / 2

        svg_final = f"""
        <svg width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="white"/>
            <g transform="translate({(width-bar_w)/2}, {start_y}) scale({bar_w/500}, {bar_h/150})">
                {content}
            </g>
            <text x="{width/2}" y="{start_y + bar_h + text_size}" 
                font-family="Arial, sans-serif" 
                font-size="{text_size}" 
                text-anchor="middle" 
                fill="black">{label}</text>
        </svg>
        """
    return svg_final

# --- DISPLAY ---
if data:
    svg_res = get_svg()
    # Rendering dell'SVG in Streamlit
    b64 = base64.b64encode(svg_res.encode('utf-8')).decode("utf-8")
    st.write(f'<img src="data:image/svg+xml;base64,{b64}" width="100%"/>', unsafe_allow_html=True)

    st.download_button(
        label="Scarica Formato Vettoriale (SVG)",
        data=svg_res,
        file_name="codice_professionale.svg",
        mime="image/svg+xml"
    )

st.info("💡 L'SVG è perfetto per la stampa: puoi ingrandirlo all'infinito senza perdere nitidezza.")
