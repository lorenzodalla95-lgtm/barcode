import streamlit as st
import qrcode
import qrcode.image.svg
import io
import base64

st.set_page_config(page_title="QR Generator PRO", layout="centered")

st.title("📐 Generatore QR Vettoriale")
st.write("Genera QR Code professionali scalabili per la stampa (SVG).")

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

st.sidebar.divider()
st.sidebar.info("Il QR e il testo verranno centrati automaticamente rispettando i margini del 10%.")

# --- INPUT ---
col1, col2 = st.columns(2)
with col1:
    data = st.text_input("Dati QR (URL/ID):", "https://google.com")
with col2:
    label = st.text_input("Testo sotto (Etichetta):", "SCANSIONAMI")

def generate_qr_svg():
    # 1. Calcolo dimensioni foglio
    w_mm, h_mm = formati_mm[scelta]
    width, height = (max(w_mm, h_mm), min(w_mm, h_mm)) if orientamento == "Orizzontale" else (min(w_mm, h_mm), max(w_mm, h_mm))

    # Margini di sicurezza (10%)
    margin = width * 0.1
    safe_w = width - (margin * 2)
    safe_h = height - (margin * 2)

    # 2. Generazione QR Vettoriale
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img_svg = qr.make_image(image_factory=factory)
    
    # Estrazione del percorso geometrico del QR
    svg_str = img_svg.to_string().decode('utf-8')
    start = svg_str.find('<path')
    end = svg_str.rfind('/>') + 2
    path_content = svg_str[start:end]
    
    # 3. Proporzionamento QR e Testo
    # Il QR occupa al massimo il 70% dell'altezza sicura per lasciare spazio al testo
    code_size = min(safe_w, safe_h * 0.7)
    
    # Dimensione base del font (circa 12% del QR)
    font_size = code_size * 0.12
    
    # Controllo lunghezza testo: se supera la larghezza del QR, lo scalo
    caratteri = len(label) if len(label) > 0 else 1
    larghezza_stimata_testo = font_size * 0.55 * caratteri # coefficiente medio per font sans-serif
    
    if larghezza_stimata_testo > code_size:
        font_size = font_size * (code_size / larghezza_stimata_testo)

    # 4. Calcolo posizioni per centratura verticale del "blocco" (QR + Spazio + Testo)
    spazio_tra_qr_e_testo = code_size * 0.15
    altezza_totale_blocco = code_size + spazio_tra_qr_e_testo + (font_size * 0.8)
    
    offset_x = (width - code_size) / 2
    offset_y = (height - altezza_totale_blocco) / 2
    
    scale_factor = code_size / img_svg.width
    text_x = width / 2
    text_y = offset_y + code_size + spazio_tra_qr_e_testo

    # 5. Assemblaggio SVG Finale
    svg_full = f"""
    <svg width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="white"/>
        <g transform="translate({offset_x}, {offset_y}) scale({scale_factor})">
            {path_content}
        </g>
        <text x="{text_x}" y="{text_y}" 
            font-family="Arial, Helvetica, sans-serif" 
            font-size="{font_size}" 
            text-anchor="middle" 
            dominant-baseline="hanging"
            fill="black">{label}</text>
    </svg>
    """
    return svg_full

# --- INTERFACCIA DI OUTPUT ---
if data:
    try:
        final_svg = generate_qr_svg()
        
        # Rendering dell'SVG nell'app
        b64 = base64.b64encode(final_svg.encode('utf-8')).decode("utf-8")
        st.write(
            f'<div style="text-align:center; background:#f0f2f6; padding:30px; border-radius:15px; border: 1px solid #ddd;">'
            f'<img src="data:image/svg+xml;base64,{b64}" style="max-width:100%; height:auto;"/>'
            f'</div>', 
            unsafe_allow_html=True
        )

        st.divider()
        
        # Download
        st.download_button(
            label="💾 Scarica QR Vettoriale (SVG)",
            data=final_svg,
            file_name=f"qr_vettoriale_{scelta.replace(' ', '_')}.svg",
            mime="image/svg+xml"
        )
        st.caption("L'SVG è ideale per la stampa: puoi ingrandirlo quanto vuoi senza sgranare.")

    except Exception as e:
        st.error(f"Si è verificato un errore nella generazione: {e}")
