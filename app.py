import streamlit as st
import qrcode
import io
from fpdf import FPDF
import pandas as pd

st.set_page_config(page_title="QR Batch Generator", layout="wide")

st.title("📑 Generatore QR Multiplo")
st.write("Compila la tabella e scarica i PDF per ogni etichetta.")

# --- CONFIGURAZIONE DIMENSIONI ---
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
    st.info("I PDF saranno generati con le dimensioni reali scelte, pronti per la stampante.")

# --- INPUT MULTIPLO (TABELLA) ---
st.subheader("Dati Etichette")
df_default = pd.DataFrame(
    [
        {"Dati QR": "https://google.com", "Testo Etichetta": "PRODOTTO A"},
        {"Dati QR": "123456789", "Testo Etichetta": "PRODOTTO B"},
    ]
)

# Editor di tabelle interattivo
edited_df = st.data_editor(
    df_default, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Dati QR": st.column_config.TextColumn("Dati QR (URL/ID)", help="Contenuto scansionabile", required=True),
        "Testo Etichetta": st.column_config.TextColumn("Testo Sotto", help="Scritta leggibile"),
    }
)

# --- LOGICA DI GENERAZIONE ---
def generate_pdf(row, w, h):
    data_qr = str(row["Dati QR"])
    label_text = str(row["Testo Etichetta"])
    
    # Setup PDF
    orient = 'L' if orientamento == "Orizzontale" else 'P'
    pdf = FPDF(orientation=orient, unit='mm', format=(w, h))
    pdf.add_page()
    
    # Calcoli proporzioni (10% margine)
    margin = w * 0.1
    safe_w = w - (margin * 2)
    safe_h = h - (margin * 2)
    
    # Generazione QR
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(data_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Dimensione QR (70% altezza utile)
    code_size = min(safe_w, safe_h * 0.7)
    
    # Dimensione Font e scaling
    font_size = code_size * 0.12
    char_len = len(label_text) if len(label_text) > 0 else 1
    if (font_size * 0.55 * char_len) > code_size:
        font_size = font_size * (code_size / (font_size * 0.55 * char_len))

    # Centratura
    ox = (w - code_size) / 2
    oy = (h - (code_size + font_size * 1.5)) / 2
    
    # Inserimento Immagine
    img_buf = io.BytesIO()
    qr_img.save(img_buf, format='PNG')
    img_buf.seek(0)
    pdf.image(img_buf, x=ox, y=oy, w=code_size, h=code_size)
    
    # Inserimento Testo
    pdf.set_font("Arial", size=font_size)
    text_w = pdf.get_string_width(label_text)
    pdf.text(x=(w - text_w) / 2, y=oy + code_size + (font_size * 1.1), txt=label_text)
    
    return bytes(pdf.output())

# --- GENERAZIONE E ANTEPRIME ---
st.divider()
st.subheader("Anteprime e Download")

# Calcolo dimensioni reali una volta sola
w_base, h_base = formati_mm[scelta]
w_real, h_real = (max(w_base, h_base), min(w_base, h_base)) if orientamento == "Orizzontale" else (min(w_base, h_base), max(w_base, h_base))

cols = st.columns(3) # Mostriamo le anteprime in 3 colonne

for index, row in edited_df.iterrows():
    if row["Dati QR"]:
        pdf_bytes = generate_pdf(row, w_real, h_real)
        
        # Mostriamo l'anteprima in un box grigio fisso (#D4D4D4)
        with cols[index % 3]:
            st.markdown(f"**Etichetta {index + 1}**")
            
            # Per l'anteprima usiamo un QR semplice (PNG) per velocità
            qr_preview = qrcode.make(row["Dati QR"], border=0)
            preview_buf = io.BytesIO()
            qr_preview.save(preview_buf, format="PNG")
            img_b64 = base64.b64encode(preview_buf.getvalue()).decode()
            
            # HTML per anteprima fissa
            st.write(
                f'''
                <div style="background:#D4D4D4; padding:20px; border-radius:8px; text-align:center; height:250px; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                    <div style="background:white; padding:10px; border-radius:4px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
                        <img src="data:image/png;base64,{img_b64}" style="width:100px; height:100px;"/>
                        <p style="color:black; font-size:12px; margin-top:5px; font-family:sans-serif;">{row["Testo Etichetta"]}</p>
                    </div>
                    <div style="margin-top:10px;"></div>
                </div>
                ''', 
                unsafe_allow_html=True
            )
            
            st.download_button(
                label=f"📥 PDF {index + 1}",
                data=pdf_bytes,
                file_name=f"qr_{index+1}.pdf",
                mime="application/pdf",
                key=f"dl_{index}",
                use_container_width=True
            )

if len(edited_df) == 0:
    st.warning("Aggiungi almeno una riga alla tabella sopra.")
