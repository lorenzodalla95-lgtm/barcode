import streamlit as st
import qrcode
import io
import base64  # <--- Fondamentale per l'anteprima
import pandas as pd
from fpdf import FPDF
import zipfile # <--- Per il download multiplo

st.set_page_config(page_title="QR Batch Generator", layout="wide")

st.title("📑 Generatore QR Multiplo Professionale")
st.write("Compila la tabella e scarica i PDF. L'anteprima è fissata per chiarezza visiva.")

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
    orientamento = st.sidebar.radio("Orientamento:", ["Verticale", "Orizzontale"])
    st.divider()
    st.info("I PDF verranno creati con le dimensioni reali in mm.")

# --- INPUT TABELLA ---
df_default = pd.DataFrame([
    {"Dati QR": "https://google.com", "Testo Etichetta": "ESEMPIO A"},
    {"Dati QR": "https://streamlit.io", "Testo Etichetta": "ESEMPIO B"},
])

edited_df = st.data_editor(df_default, num_rows="dynamic", use_container_width=True)

# --- LOGICA PDF ---
def generate_pdf(row, w, h):
    data_qr = str(row["Dati QR"])
    label_text = str(row["Testo Etichetta"])
    
    orient = 'L' if orientamento == "Orizzontale" else 'P'
    pdf = FPDF(orientation=orient, unit='mm', format=(w, h))
    pdf.add_page()
    
    # Margini e proporzioni
    margin = w * 0.1
    code_size = min(w - (margin*2), (h - (margin*2)) * 0.7)
    
    # Generazione QR
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(data_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Font scaling
    font_size = code_size * 0.12
    if (font_size * 0.55 * len(label_text)) > code_size:
        font_size = font_size * (code_size / (font_size * 0.55 * len(label_text)))

    # Posizionamento
    ox = (w - code_size) / 2
    oy = (h - (code_size + font_size * 1.5)) / 2
    
    img_buf = io.BytesIO()
    qr_img.save(img_buf, format='PNG')
    img_buf.seek(0)
    pdf.image(img_buf, x=ox, y=oy, w=code_size, h=code_size)
    
    pdf.set_font("Arial", size=font_size)
    pdf.text(x=(w - pdf.get_string_width(label_text)) / 2, y=oy + code_size + (font_size * 1.1), txt=label_text)
    
    return bytes(pdf.output())

# --- GENERAZIONE E VISUALIZZAZIONE ---
if not edited_df.empty:
    w_base, h_base = formati_mm[scelta]
    w_real, h_real = (max(w_base, h_base), min(w_base, h_base)) if orientamento == "Orizzontale" else (min(w_base, h_base), max(w_base, h_base))

    # Creiamo una lista per lo ZIP
    all_pdfs = []

    st.divider()
    cols = st.columns(4)

    for index, row in edited_df.iterrows():
        if row["Dati QR"]:
            pdf_bytes = generate_pdf(row, w_real, h_real)
            all_pdfs.append((f"etichetta_{index+1}.pdf", pdf_bytes))
            
            with cols[index % 4]:
                # Anteprima fissa con sfondo #D4D4D4
                qr_prev = qrcode.make(row["Dati QR"], border=0)
                p_buf = io.BytesIO()
                qr_prev.save(p_buf, format="PNG")
                img_b64 = base64.b64encode(p_buf.getvalue()).decode()
                
                st.write(f'''
                    <div style="background:#D4D4D4; padding:15px; border-radius:10px; text-align:center; margin-bottom:10px;">
                        <div style="background:white; padding:10px; display:inline-block; border-radius:5px;">
                            <img src="data:image/png;base64,{img_b64}" width="80"/>
                            <div style="color:black; font-size:10px; font-family:sans-serif; margin-top:5px; max-width:100px; overflow:hidden;">{row["Testo Etichetta"]}</div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.download_button(f"📄 PDF {index+1}", pdf_bytes, f"qr_{index+1}.pdf", "application/pdf", key=f"btn_{index}", use_container_width=True)

    # --- TASTO ZIP CUMULATIVO ---
    if all_pdfs:
        st.divider()
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zip_file:
            for name, data in all_pdfs:
                zip_file.writestr(name, data)
        
        st.download_button(
            label="📦 SCARICA TUTTE LE ETICHETTE (ZIP)",
            data=zip_buf.getvalue(),
            file_name="etichette_qr.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )
