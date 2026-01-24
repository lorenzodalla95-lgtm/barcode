import streamlit as st
import qrcode
import io
import base64
import pandas as pd
from fpdf import FPDF
import zipfile

st.set_page_config(page_title="QR Batch PRO", layout="wide")

st.title("📑 Generatore QR Multiplo Professionale")

# --- CONFIGURAZIONE ---
formati_mm = {
    "Etichetta Piccola (50x30mm)": (50, 30),
    "Etichetta Media (100x50mm)": (100, 50),
    "A6": (105, 148),
    "A5": (148, 210),
    "A4": (210, 297),
}

with st.sidebar:
    st.header("Configurazione Stampa")
    scelta = st.selectbox("Dimensione Etichetta:", list(formati_mm.keys()))
    orientamento = st.radio("Orientamento:", ["Verticale", "Orizzontale"])
    st.divider()
    st.info("Il testo viene scalato automaticamente per la massima leggibilità.")

# --- INPUT TABELLA ---
st.subheader("1. Inserisci i dati")
df_default = pd.DataFrame([
    {"Dati QR": "https://google.com", "Testo Etichetta": "ESEMPIO A"},
    {"Dati QR": "12345", "Testo Etichetta": "CODICE 01"},
])
edited_df = st.data_editor(df_default, num_rows="dynamic", use_container_width=True)

# --- FUNZIONE LOGICA CORE ---
def get_dimensions():
    w_base, h_base = formati_mm[scelta]
    if orientamento == "Orizzontale":
        return max(w_base, h_base), min(w_base, h_base)
    return min(w_base, h_base), max(w_base, h_base)

def generate_pdf(row, w, h):
    data_qr = str(row["Dati QR"])
    label_text = str(row["Testo Etichetta"])
    
    pdf = FPDF(orientation='L' if w > h else 'P', unit='mm', format=(w, h))
    pdf.add_page()
    
    # Proporzioni dinamiche: il testo deve essere leggibile
    # Impostiamo il font al 15% dell'altezza o proporzionato alla larghezza
    font_size = min(h * 0.15, w * 0.08) 
    
    # Scaling per testi lunghi
    text_width_limit = w * 0.9
    pdf.set_font("Arial", size=font_size)
    actual_text_w = pdf.get_string_width(label_text)
    if actual_text_w > text_width_limit:
        font_size *= (text_width_limit / actual_text_w)
        pdf.set_font("Arial", size=font_size)

    # Il QR occupa lo spazio rimanente (margine 10%)
    qr_max_h = h - font_size - (h * 0.2) # spazio per margini e testo
    code_size = min(w * 0.8, qr_max_h)
    
    # Generazione QR
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(data_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Centratura verticale del blocco
    total_content_h = code_size + (font_size * 1.2)
    offset_x = (w - code_size) / 2
    offset_y = (h - total_content_h) / 2
    
    # Inserimento Immagine
    img_buf = io.BytesIO()
    qr_img.save(img_buf, format='PNG')
    pdf.image(img_buf, x=offset_x, y=offset_y, w=code_size, h=code_size)
    
    # Inserimento Testo
    pdf.text(x=(w - pdf.get_string_width(label_text)) / 2, y=offset_y + code_size + (font_size * 1), txt=label_text)
    
    return bytes(pdf.output())

# --- GENERAZIONE E VISUALIZZAZIONE ---
if not edited_df.empty:
    w_real, h_real = get_dimensions()
    all_pdfs = []

    st.divider()
    st.subheader("2. Anteprime e Download")
    
    # Calcolo proporzione per anteprima visiva (CSS)
    ratio = h_real / w_real
    preview_w = 200 # larghezza fissa in pixel per l'anteprima
    preview_h = int(preview_w * ratio)

    cols = st.columns(3)

    for index, row in edited_df.iterrows():
        if row["Dati QR"]:
            pdf_bytes = generate_pdf(row, w_real, h_real)
            all_pdfs.append((f"qr_{index+1}.pdf", pdf_bytes))
            
            with cols[index % 3]:
                # Generazione immagine QR per anteprima
                qr_p = qrcode.make(row["Dati QR"], border=0)
                p_buf = io.BytesIO()
                qr_p.save(p_buf, format="PNG")
                img_b64 = base64.b64encode(p_buf.getvalue()).decode()
                
                # HTML Anteprima Dinamica
                st.write(f'''
                    <div style="background:#D4D4D4; padding:20px; border-radius:10px; display:flex; justify-content:center; align-items:center;">
                        <div style="background:white; width:{preview_w}px; height:{preview_h}px; display:flex; flex-direction:column; justify-content:center; align-items:center; border:1px solid #999; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                            <img src="data:image/png;base64,{img_b64}" style="width:50%; height:auto;"/>
                            <div style="color:black; font-size:14px; font-weight:bold; font-family:sans-serif; margin-top:10px; text-align:center; padding:0 5px; width:100%; word-wrap: break-word;">
                                {row["Testo Etichetta"]}
                            </div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.download_button(f"📄 Scarica PDF {index+1}", pdf_bytes, f"qr_{index+1}.pdf", key=f"b_{index}", use_container_width=True)

    if all_pdfs:
        st.divider()
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            for name, data in all_pdfs:
                z.writestr(name, data)
        
        st.download_button("📦 SCARICA TUTTI (ZIP)", zip_buf.getvalue(), "etichette.zip", "application/zip", use_container_width=True, type="primary")
