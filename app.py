import streamlit as st
import qrcode
import io
import base64
import pandas as pd
from fpdf import FPDF
import zipfile

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="QR Batch PRO", layout="wide")

# CSS per pulizia estetica e distanziamento
st.markdown("""
    <style>
    .stDownloadButton { margin-top: -10px; }
    .stDataEditor { margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📑 QR PRO: Generatore Etichette Fedele")

# --- 1. BARRA LATERALE (CONFIGURAZIONE) ---
formati_mm = {
    "Etichetta Piccola (50x30mm)": (50, 30),
    "Etichetta Media (100x50mm)": (100, 50),
    "A6": (105, 148),
    "A5": (148, 210),
    "A4": (210, 297),
}

with st.sidebar:
    st.header("📏 Impostazioni Stampa")
    scelta = st.selectbox("Formato carta:", list(formati_mm.keys()))
    orientamento = st.radio("Orientamento:", ["Verticale", "Orizzontale"])
    
    st.divider()
    st.header("🔍 Regolazione Layout")
    # Lo slider ora agisce in modo millimetrico
    qr_scale = st.slider("Ingrandimento QR (%)", 40, 98, 85)
    
    st.divider()
    st.caption("Logica: Sfondo #D4D4D4 | Solo export PDF")

# --- 2. CALCOLO DIMENSIONI REALI ---
def get_dims():
    w_base, h_base = formati_mm[scelta]
    if orientamento == "Orizzontale":
        return max(w_base, h_base), min(w_base, h_base)
    return min(w_base, h_base), max(w_base, h_base)

w_mm, h_mm = get_dims()

# --- 3. TABELLA INPUT ---
st.subheader("1. Dati Etichette")
df_init = pd.DataFrame([
    {"Dati QR": "https://google.com", "Testo Etichetta": "PRODOTTO A"},
    {"Dati QR": "ABC-123", "Testo Etichetta": "LOTTO 001"},
])
edited_df = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

# --- 4. FUNZIONE GENERAZIONE PDF (LOGICA UNIFICATA) ---
def generate_pdf(row, w, h, scale_pct):
    data_qr = str(row["Dati QR"])
    text = str(row["Testo Etichetta"])
    
    pdf = FPDF(unit='mm', format=(w, h))
    pdf.add_page()
    
    # Parametri geometrici (2% margine)
    safe_margin = min(w, h) * 0.02
    font_size = h * 0.12 if text else 0
    padding = font_size * 0.2
    
    # Calcolo lato QR massimizzato
    max_h = (h - (safe_margin * 2)) - font_size - padding
    max_w = w - (safe_margin * 2)
    side_mm = min(max_w, max_h) * (scale_pct / 100)
    
    # Generazione QR
    qr_obj = qrcode.QRCode(box_size=10, border=0)
    qr_obj.add_data(data_qr)
    qr_obj.make(fit=True)
    img = qr_obj.make_image(fill_color="black", back_color="white")
    
    # Posizionamento centrato
    total_h = side_mm + padding + (font_size * 0.8)
    ox = (w - side_mm) / 2
    oy = (h - total_h) / 2
    
    # Render PDF
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    pdf.image(buf, x=ox, y=oy, w=side_mm, h=side_mm)
    
    if text:
        pdf.set_font("Arial", size=font_size)
        # Scaling testo se troppo largo
        if pdf.get_string_width(text) > w * 0.9:
            pdf.set_font("Arial", size=font_size * (w * 0.9 / pdf.get_string_width(text)))
        pdf.text(x=(w - pdf.get_string_width(text))/2, y=oy + side_mm + (font_size * 0.85), txt=text)
    
    return bytes(pdf.output()), side_mm, font_size, oy, padding

# --- 5. VISUALIZZAZIONE ANTEPRIME E DOWNLOAD ---
if not edited_df.empty:
    all_pdfs = []
    st.divider()
    st.subheader("2. Anteprime e Download")
    
    cols = st.columns(3)
    
    for idx, row in edited_df.iterrows():
        if row["Dati QR"]:
            # Generiamo il PDF e recuperiamo le misure reali usate per l'anteprima
            pdf_bytes, q_mm, f_mm, offset_y_mm, pad_mm = generate_pdf(row, w_mm, h_mm, qr_scale)
            all_pdfs.append((f"etichetta_{idx+1}.pdf", pdf_bytes))
            
            with cols[idx % 3]:
                # Calcolo zoom per l'anteprima a video (1mm = 3.5px)
                z = 3.5
                preview_w, preview_h = w_mm * z, h_mm * z
                q_px, f_px, pad_px = q_mm * z, f_mm * z, pad_mm * z
                
                # Immagine QR per HTML
                q_img = qrcode.make(row["Dati QR"], border=0)
                b = io.BytesIO()
                q_img.save(b, format="PNG")
                b64 = base64.b64encode(b.getvalue()).decode()
                
                # HTML Anteprima Speculare al PDF
                st.write(f'''
                    <div style="background:#D4D4D4; padding:25px; border-radius:10px; display:flex; flex-direction:column; align-items:center; margin-bottom:20px;">
                        <div style="
                            background:white; 
                            width:{preview_w}px; 
                            height:{preview_h}px; 
                            position:relative; 
                            border:1px solid #666; 
                            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                            display:flex; flex-direction:column; align-items:center; justify-content:center;
                        ">
                            <img src="data:image/png;base64,{b64}" style="width:{q_px}px; height:{q_px}px;"/>
                            <div style="
                                color:black; font-family:Arial; font-size:{f_px}px; 
                                margin-top:{pad_px}px; text-align:center; width:90%;
                                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                            ">
                                {row["Testo Etichetta"]}
                            </div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.download_button(
                    label=f"📥 PDF {idx+1}", 
                    data=pdf_bytes, 
                    file_name=f"qr_{idx+1}.pdf", 
                    key=f"dl_{idx}", 
                    use_container_width=True
                )

    # --- 6. DOWNLOAD ZIP ---
    if all_pdfs:
        st.divider()
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for name, data in all_pdfs:
                zf.writestr(name, data)
        
        st.download_button(
            label="📦 SCARICA TUTTE LE ETICHETTE (ZIP)",
            data=zip_buf.getvalue(),
            file_name="batch_qr_labels.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )

# --- MESSAGGIO SE VUOTO ---
else:
    st.info("Aggiungi righe alla tabella per iniziare.")
