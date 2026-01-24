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

# --- 2. INPUT DATI ---
st.subheader("1. Dati Etichette")
df_init = pd.DataFrame([
    {"Dati QR": "https://google.com", "Testo Etichetta": "PRODOTTO A"},
    {"Dati QR": "ABC-123", "Testo Etichetta": "LOTTO 001"},
])
edited_df = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

# --- 3. LOGICA PDF ---
def generate_pdf(row, w, h, scale_pct):
    data_qr = str(row["Dati QR"])
    text = str(row["Testo Etichetta"])
    pdf = FPDF(unit='mm', format=(w, h))
    pdf.add_page()
    
    safe_margin = min(w, h) * 0.02
    font_size = h * 0.12 if text else 0
    padding = font_size * 0.2
    
    max_h = (h - (safe_margin * 2)) - font_size - padding
    max_w = w - (safe_margin * 2)
    side_mm = min(max_w, max_h) * (scale_pct / 100)
    
    qr_obj = qrcode.QRCode(box_size=10, border=0)
    qr_obj.add_data(data_qr)
    qr_obj.make(fit=True)
    img = qr_obj.make_image(fill_color="black", back_color="white")
    
    total_h = side_mm + padding + (font_size * 0.8)
    ox = (w - side_mm) / 2
    oy = (h - total_h) / 2
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    pdf.image(buf, x=ox, y=oy, w=side_mm, h=side_mm)
    
    if text:
        pdf.set_font("Arial", size=font_size)
        if pdf.get_string_width(text) > w * 0.9:
            pdf.set_font("Arial", size=font_size * (w * 0.9 / pdf.get_string_width(text)))
        pdf.text(x=(w - pdf.get_string_width(text))/2, y=oy + side_mm + (font_size * 0.85), txt=text)
    
    return bytes(pdf.output())

# --- 4. ANTEPRIMA E DOWNLOAD ---
if not edited_df.empty:
    all_pdfs = []
    st.divider()
    st.subheader("2. Anteprime")
    
    cols = st.columns(3)
    
    for idx, row in edited_df.iterrows():
        if row["Dati QR"]:
            pdf_bytes = generate_pdf(row, w_mm, h_mm, qr_scale)
            all_pdfs.append((f"etichetta_{idx+1}.pdf", pdf_bytes))
            
            with cols[idx % 3]:
                # Calcolo proporzioni per l'anteprima CSS
                # Fissiamo il box grigio a 250px di altezza
                container_h = 250
                ratio = w_mm / h_mm
                
                # Calcoliamo larghezza e altezza del "foglietto" bianco 
                # in modo che stia sempre dentro il box 250x250
                if ratio > 1: # Orizzontale
                    p_w = 200
                    p_h = 200 / ratio
                else: # Verticale
                    p_h = 200
                    p_w = 200 * ratio

                q_img = qrcode.make(row["Dati QR"], border=0)
                b = io.BytesIO()
                q_img.save(b, format="PNG")
                b64 = base64.b64encode(b.getvalue()).decode()
                
                # HTML con Flexbox per centrare perfettamente
                st.write(f'''
                    <div style="background:#D4D4D4; height:{container_h}px; border-radius:10px; display:flex; justify-content:center; align-items:center; margin-bottom:10px;">
                        <div style="background:white; width:{p_w}px; height:{p_h}px; display:flex; flex-direction:column; justify-content:center; align-items:center; box-shadow: 0 4px 8px rgba(0,0,0,0.2); overflow:hidden; padding:5px;">
                            <img src="data:image/png;base64,{b64}" style="width:{qr_scale}%; height:auto;"/>
                            <div style="color:black; font-family:Arial; font-size:10px; font-weight:bold; margin-top:2px; text-align:center; width:90%; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                                {row["Testo Etichetta"]}
                            </div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.download_button(f"📥 PDF {idx+1}", pdf_bytes, f"qr_{idx+1}.pdf", key=f"dl_{idx}", use_container_width=True)

    if all_pdfs:
        st.divider()
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for name, data in all_pdfs:
                zf.writestr(name, data)
        st.download_button("📦 SCARICA TUTTO (ZIP)", zip_buf.getvalue(), "etichette.zip", "application/zip", use_container_width=True, type="primary")
