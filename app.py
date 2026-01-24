import streamlit as st
import qrcode
import io
import base64
import pandas as pd
from fpdf import FPDF
import zipfile

st.set_page_config(page_title="QR Batch PRO", layout="wide")

# --- 1. CONFIGURAZIONE DIMENSIONI ---
formati_mm = {
    "Etichetta Piccola (50x30mm)": (50, 30),
    "Etichetta Media (100x50mm)": (100, 50),
    "A6": (105, 148),
    "A5": (148, 210),
    "A4": (210, 297),
}

with st.sidebar:
    st.header("📏 Impostazioni")
    scelta = st.selectbox("Formato carta:", list(formati_mm.keys()))
    orientamento = st.radio("Orientamento:", ["Verticale", "Orizzontale"])
    st.divider()
    qr_scale = st.slider("Ingrandimento QR (%)", 40, 98, 85)

def get_dims():
    w_base, h_base = formati_mm[scelta]
    if orientamento == "Orizzontale":
        return max(w_base, h_base), min(w_base, h_base)
    return min(w_base, h_base), max(w_base, h_base)

w_mm, h_mm = get_dims()

# --- 2. LOGICA MATEMATICA UNIFICATA ---
def get_layout_math(w, h, scale_pct, text):
    safe_margin = min(w, h) * 0.02
    font_size = h * 0.12 if text else 0
    padding = font_size * 0.2
    
    max_h = (h - (safe_margin * 2)) - font_size - padding
    max_w = w - (safe_margin * 2)
    side_mm = min(max_w, max_h) * (scale_pct / 100)
    
    # Altezza totale del blocco (QR + Spazio + Altezza ottica testo)
    total_content_h = side_mm + padding + (font_size * 0.8)
    
    ox = (w - side_mm) / 2
    oy = (h - total_content_h) / 2
    
    return side_mm, font_size, ox, oy, padding

# --- 3. FUNZIONE PDF ---
def generate_pdf(row, w, h, scale_pct):
    text = str(row["Testo Etichetta"])
    side_mm, font_size, ox, oy, padding = get_layout_math(w, h, scale_pct, text)
    
    pdf = FPDF(unit='mm', format=(w, h))
    pdf.add_page()
    
    qr_obj = qrcode.QRCode(box_size=10, border=0)
    qr_obj.add_data(str(row["Dati QR"]))
    qr_obj.make(fit=True)
    img = qr_obj.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    pdf.image(buf, x=ox, y=oy, w=side_mm, h=side_mm)
    
    if text:
        pdf.set_font("Arial", size=font_size)
        if pdf.get_string_width(text) > w * 0.95:
            pdf.set_font("Arial", size=font_size * (w * 0.95 / pdf.get_string_width(text)))
        # La coordinata Y nel PDF è la baseline
        pdf.text(x=(w - pdf.get_string_width(text))/2, y=oy + side_mm + (font_size * 0.85), txt=text)
    
    return bytes(pdf.output())

# --- 4. INTERFACCIA E ANTEPRIME ---
st.subheader("1. Dati Etichette")
df_init = pd.DataFrame([
    {"Dati QR": "https://google.com", "Testo Etichetta": "TEST PRODOTTO"},
    {"Dati QR": "ID-9999", "Testo Etichetta": "DESCRIZIONE BREVE"},
])
edited_df = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

if not edited_df.empty:
    all_pdfs = []
    st.divider()
    st.subheader("2. Anteprime (Rendering 1:1)")
    
    cols = st.columns(3)
    
    for idx, row in edited_df.iterrows():
        if row["Dati QR"]:
            pdf_bytes = generate_pdf(row, w_mm, h_mm, qr_scale)
            all_pdfs.append((f"etichetta_{idx+1}.pdf", pdf_bytes))
            
            side_mm, f_mm, ox_mm, oy_mm, pad_mm = get_layout_math(w_mm, h_mm, qr_scale, row["Testo Etichetta"])
            
            with cols[idx % 3]:
                display_max = 200
                scale_factor = display_max / max(w_mm, h_mm)
                
                p_w, p_h = w_mm * scale_factor, h_mm * scale_factor
                q_px = side_mm * scale_factor
                f_px = f_mm * scale_factor
                ox_px = ox_mm * scale_factor
                oy_px = oy_mm * scale_factor
                
                q_img = qrcode.make(row["Dati QR"], border=0)
                b = io.BytesIO()
                q_img.save(b, format="PNG")
                b64 = base64.b64encode(b.getvalue()).decode()
                
                # HTML CORRETTO: oy_px + q_px sposta il testo esattamente sotto il QR
                # Il padding assicura il distacco millimetrico calcolato
                text_top = oy_px + q_px + (pad_mm * scale_factor)

                st.write(f'''
                    <div style="background:#D4D4D4; height:260px; border-radius:10px; display:flex; justify-content:center; align-items:center; margin-bottom:10px;">
                        <div style="background:white; width:{p_w}px; height:{p_h}px; position:relative; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                            <img src="data:image/png;base64,{b64}" style="
                                position: absolute;
                                left: {ox_px}px;
                                top: {oy_px}px;
                                width: {q_px}px;
                                height: {q_px}px;
                            "/>
                            <div style="
                                position: absolute;
                                left: 0;
                                top: {text_top}px;
                                width: 100%;
                                height: {f_px}px;
                                line-height: 0.9;
                                text-align: center;
                                color: black;
                                font-family: Arial, sans-serif;
                                font-size: {f_px}px;
                                white-space: nowrap;
                                overflow: hidden;
                            ">
                                {row["Testo Etichetta"]}
                            </div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.download_button(f"📥 Scarica PDF {idx+1}", pdf_bytes, f"qr_{idx+1}.pdf", key=f"dl_{idx}", use_container_width=True)

    if all_pdfs:
        st.divider()
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for name, data in all_pdfs:
                zf.writestr(name, data)
        st.download_button("📦 SCARICA TUTTO LO ZIP", zip_buf.getvalue(), "archivio_etichette.zip", "application/zip", use_container_width=True, type="primary")
