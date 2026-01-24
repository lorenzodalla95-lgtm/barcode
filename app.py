import streamlit as st
import qrcode
import io
import base64
import pandas as pd
from fpdf import FPDF
import zipfile

st.set_page_config(page_title="QR Batch PRO", layout="wide")

# Costante universale: 1mm = 2.83464567 punti (pt)
MM_TO_PT = 2.83464567

# --- 1. CONFIGURAZIONE ---
formati_mm = {
    "Etichetta Piccola (50x30mm)": (50, 30),
    "Etichetta Media (100x50mm)": (100, 50),
    "A6": (105, 148),
    "A5": (148, 210),
    "A4": (210, 297),
}

with st.sidebar:
    st.header("📏 Configurazione")
    scelta = st.selectbox("Formato carta:", list(formati_mm.keys()))
    orientamento = st.radio("Orientamento:", ["Verticale", "Orizzontale"])
    st.divider()
    qr_scale = st.slider("Ingrandimento QR (%)", 40, 98, 80)

def get_dims():
    w_base, h_base = formati_mm[scelta]
    if orientamento == "Orizzontale":
        return max(w_base, h_base), min(w_base, h_base)
    return min(w_base, h_base), max(w_base, h_base)

w_mm, h_mm = get_dims()

# --- 2. MATEMATICA DI POSIZIONAMENTO (IDENTICA PER PDF E HTML) ---
def get_layout(w, h, scale_pct, text):
    # Margine di sicurezza esterno (3%)
    margin = min(w, h) * 0.03
    # Altezza dedicata al font (10% dell'altezza totale)
    f_size_mm = h * 0.10 if text else 0
    # Distanza tra QR e testo (2% dell'altezza totale)
    gap_mm = h * 0.02 if text else 0
    
    # Calcolo lato QR (spazio rimanente)
    avail_h = h - (margin * 2) - f_size_mm - gap_mm
    avail_w = w - (margin * 2)
    qr_side = min(avail_w, avail_h) * (scale_pct / 100)
    
    # Centratura verticale del blocco QR + Testo
    block_h = qr_side + gap_mm + f_size_mm
    x_off = (w - qr_side) / 2
    y_off = (h - block_h) / 2
    
    return qr_side, f_size_mm, x_off, y_off, gap_mm

# --- 3. GENERAZIONE PDF ---
def generate_pdf(row, w, h, scale_pct):
    text = str(row["Testo Etichetta"])
    qr_side, f_mm, x_off, y_off, gap = get_layout(w, h, scale_pct, text)
    
    pdf = FPDF(unit='mm', format=(w, h))
    pdf.add_page()
    
    # QR Code
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(str(row["Dati QR"]))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    pdf.image(buf, x=x_off, y=y_off, w=qr_side, h=qr_side)
    
    # Testo
    if text:
        # Importante: in FPDF size è in punti (pt)
        pdf.set_font("Arial", size=f_mm * MM_TO_PT)
        
        # Se il testo è troppo largo, lo rimpiccioliamo
        text_w = pdf.get_string_width(text)
        current_f = f_mm * MM_TO_PT
        if text_w > w * 0.9:
            current_f *= (w * 0.9 / text_w)
            pdf.set_font("Arial", size=current_f)
        
        # Posizionamento: y_off + qr_side + gap + altezza font
        # FPDF scrive sulla baseline, quindi aggiungiamo l'altezza del font
        pdf.text(x=(w - pdf.get_string_width(text))/2, 
                 y=y_off + qr_side + gap + (f_mm * 0.8), 
                 txt=text)
    
    return bytes(pdf.output())

# --- 4. INTERFACCIA ---
st.subheader("1. Inserimento Dati")
df = st.data_editor(pd.DataFrame([{"Dati QR": "ABC.123", "Testo Etichetta": "ETICHETTA TEST"}]), num_rows="dynamic", use_container_width=True)

if not df.empty:
    st.divider()
    st.subheader("2. Anteprime (Rapporto reale)")
    cols = st.columns(3)
    
    all_pdfs = []
    
    for idx, row in df.iterrows():
        if row["Dati QR"]:
            pdf_b = generate_pdf(row, w_mm, h_mm, qr_scale)
            all_pdfs.append((f"qr_{idx}.pdf", pdf_b))
            
            # Recupero coordinate
            qr_s, f_m, x_m, y_m, gp_m = get_layout(w_mm, h_mm, qr_scale, row["Testo Etichetta"])
            
            with cols[idx % 3]:
                # Zoom per l'anteprima (max 220px)
                z = 220 / max(w_mm, h_mm)
                
                # Conversione millimetri -> pixel per CSS
                box_w, box_h = w_mm * z, h_mm * z
                qr_px, f_px = qr_s * z, f_m * z
                x_px, y_px, gap_px = x_m * z, y_m * z, gp_m * z
                
                q_img = qrcode.make(row["Dati QR"], border=0)
                buf_q = io.BytesIO()
                q_img.save(buf_q, format="PNG")
                b64 = base64.b64encode(buf_q.getvalue()).decode()
                
                # HTML MILIMETRICO
                st.write(f'''
                    <div style="background:#D4D4D4; height:280px; display:flex; justify-content:center; align-items:center; border-radius:8px; margin-bottom:10px;">
                        <div style="
                            background:white; 
                            width:{box_w}px; height:{box_h}px; 
                            position:relative; 
                            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                        ">
                            <img src="data:image/png;base64,{b64}" style="
                                position: absolute;
                                left: {x_px}px; top: {y_px}px;
                                width: {qr_px}px; height: {qr_px}px;
                            "/>
                            <div style="
                                position: absolute;
                                left: 0;
                                top: {y_px + qr_px + gap_px}px;
                                width: 100%;
                                height: {f_px}px;
                                line-height: {f_px}px;
                                font-family: Arial;
                                font-size: {f_px}px;
                                text-align: center;
                                color: black;
                                white-space: nowrap;
                                overflow: hidden;
                            ">
                                {row["Testo Etichetta"]}
                            </div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.download_button(f"📥 Scarica PDF {idx+1}", pdf_b, f"etichetta_{idx}.pdf", key=f"d_{idx}", use_container_width=True)

    if all_pdfs:
        st.divider()
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w") as z:
            for n, d in all_pdfs: z.writestr(n, d)
        st.download_button("📦 SCARICA TUTTI (ZIP)", zip_io.getvalue(), "etichette.zip", use_container_width=True, type="primary")
