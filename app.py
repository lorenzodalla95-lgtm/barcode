import streamlit as st
import qrcode
import io
import base64
import pandas as pd
from fpdf import FPDF
import zipfile

st.set_page_config(page_title="QR Batch PRO", layout="wide")

st.title("📑 QR PRO: Generazione Multipla")

# --- 1. CONFIGURAZIONE DIMENSIONI ---
formati_mm = {
    "Etichetta Piccola (50x30mm)": (50, 30),
    "Etichetta Media (100x50mm)": (100, 50),
    "A6": (105, 148),
    "A5": (148, 210),
    "A4": (210, 297),
}

with st.sidebar:
    st.header("Impostazioni Stampa")
    scelta = st.selectbox("Dimensione Base:", list(formati_mm.keys()))
    orientamento = st.radio("Orientamento:", ["Verticale", "Orizzontale"])
    st.divider()
    st.info("Sfondo anteprima fissato su #D4D4D4. Solo export PDF.")

# --- 2. LOGICA DIMENSIONI ---
def get_final_dims():
    w_base, h_base = formati_mm[scelta]
    if orientamento == "Orizzontale":
        return max(w_base, h_base), min(w_base, h_base)
    return min(w_base, h_base), max(w_base, h_base)

# --- 3. INPUT DATI ---
st.subheader("Inserisci i dati nella tabella")
df_init = pd.DataFrame([
    {"Dati QR": "https://google.com", "Testo Etichetta": "PRODOTTO 01"},
    {"Dati QR": "https://streamlit.io", "Testo Etichetta": "PRODOTTO 02"},
])
edited_df = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

# --- 4. FUNZIONE GENERAZIONE PDF ---
def generate_pdf(row, w, h):
    data_qr = str(row["Dati QR"])
    label_text = str(row["Testo Etichetta"])
    
    pdf = FPDF(unit='mm', format=(w, h))
    pdf.add_page()
    
    # Calcolo proporzioni font
    font_size = min(h * 0.18, w * 0.12)
    pdf.set_font("Arial", size=font_size)
    
    limit_w = w * 0.9
    tw = pdf.get_string_width(label_text)
    if tw > limit_w:
        font_size *= (limit_w / tw)
        pdf.set_font("Arial", size=font_size)

    qr_max_h = h - font_size - (h * 0.2)
    code_size = min(w * 0.8, qr_max_h)
    
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(data_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    total_h = code_size + (font_size * 1.1)
    ox = (w - code_size) / 2
    oy = (h - total_h) / 2
    
    img_buf = io.BytesIO()
    qr_img.save(img_buf, format='PNG')
    pdf.image(img_buf, x=ox, y=oy, w=code_size, h=code_size)
    pdf.text(x=(w - pdf.get_string_width(label_text))/2, y=oy + code_size + (font_size * 0.9), txt=label_text)
    
    return bytes(pdf.output())

# --- 5. VISUALIZZAZIONE E DOWNLOAD ---
if not edited_df.empty:
    w_mm, h_mm = get_final_dims()
    all_pdfs = []
    
    st.divider()
    st.write(f"**Anteprime (Formato reale: {w_mm}x{h_mm} mm)**")
    
    cols = st.columns(3)
    
    preview_w = 180
    preview_h = int(preview_w * (h_mm / w_mm))

    for idx, row in edited_df.iterrows():
        if row["Dati QR"]:
            try:
                pdf_data = generate_pdf(row, w_mm, h_mm)
                all_pdfs.append((f"qr_{idx+1}.pdf", pdf_data))
                
                with cols[idx % 3]:
                    # QR per anteprima
                    q = qrcode.make(row["Dati QR"], border=0)
                    b = io.BytesIO()
                    q.save(b, format="PNG")
                    b64 = base64.b64encode(b.getvalue()).decode()
                    
                    # HTML Anteprima con margin-bottom per distanziare dal tasto
                    st.write(f'''
                        <div style="background:#D4D4D4; padding:20px; border-radius:12px; display:flex; justify-content:center; align-items:center; min-height:260px; margin-bottom: 25px;">
                            <div style="background:white; width:{preview_w}px; height:{preview_h}px; display:flex; flex-direction:column; justify-content:center; align-items:center; border:1px solid #888; box-shadow: 2px 4px 12px rgba(0,0,0,0.15);">
                                <img src="data:image/png;base64,{b64}" style="width:40%; height:auto;"/>
                                <div style="color:black; font-family:sans-serif; font-size:12px; font-weight:bold; margin-top:10px; text-align:center; padding:0 8px; width:100%; word-wrap: break-word;">
                                    {row["Testo Etichetta"]}
                                </div>
                            </div>
                        </div>
                    ''', unsafe_allow_html=True)
                    
                    # Tasto download
                    st.download_button(
                        label=f"📥 Scarica PDF {idx+1}", 
                        data=pdf_data, 
                        file_name=f"etichetta_{idx+1}.pdf", 
                        key=f"btn_{idx}", 
                        use_container_width=True
                    )
                    st.markdown("<br>", unsafe_allow_html=True) # Spazio ulteriore tra le righe di card

            except Exception as e:
                st.error(f"Errore riga {idx+1}: {e}")

    if all_pdfs:
        st.divider()
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w") as z:
            for name, data in all_pdfs:
                z.writestr(name, data)
        
        st.download_button(
            label="📦 SCARICA TUTTI I PDF (ZIP)",
            data=zip_io.getvalue(),
            file_name="etichette_qr.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )
