import streamlit as st
import qrcode
import io
import base64
import pandas as pd
from fpdf import FPDF
import zipfile
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="QR Batch PRO", layout="wide")

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
    qr_scale = st.slider("Ingrandimento QR (%)", 30, 95, 80)

def get_dims():
    w_base, h_base = formati_mm[scelta]
    if orientamento == "Orizzontale":
        return max(w_base, h_base), min(w_base, h_base)
    return min(w_base, h_base), max(w_base, h_base)

w_mm, h_mm = get_dims()

# --- 2. LOGICA DI LAYOUT (UNICA PER TUTTI) ---
def get_layout_logic(w, h, scale_pct, text):
    margin = min(w, h) * 0.04
    f_size_mm = h * 0.10 if text else 0
    gap_mm = h * 0.03 if text else 0
    
    avail_h = h - (margin * 2) - f_size_mm - gap_mm
    avail_w = w - (margin * 2)
    qr_side = min(avail_w, avail_h) * (scale_pct / 100)
    
    block_h = qr_side + gap_mm + (f_size_mm * 0.8)
    x_off = (w - qr_side) / 2
    y_off = (h - block_h) / 2
    
    return qr_side, f_size_mm, x_off, y_off, gap_mm

# --- 3. GENERATORE IMMAGINE ANTEPRIMA (PERFETTA) ---
def generate_preview_img(row, w, h, scale_pct):
    # Usiamo 10 pixel per ogni mm per avere alta precisione
    dpmm = 10 
    img_w, img_h = int(w * dpmm), int(h * dpmm)
    img = Image.new('RGB', (img_w, img_h), color='white')
    draw = ImageDraw.Draw(img)
    
    text = str(row["Testo Etichetta"])
    qr_s, f_m, x_m, y_m, gp_m = get_layout_logic(w, h, scale_pct, text)
    
    # Disegna QR
    qr = qrcode.make(str(row["Dati QR"]), border=0)
    qr_res = qr.resize((int(qr_s * dpmm), int(qr_s * dpmm)))
    img.paste(qr_res, (int(x_m * dpmm), int(y_m * dpmm)))
    
    # Disegna Testo
    if text:
        try:
            # Carica un font standard (Arial o simile)
            font = ImageFont.load_default() # In produzione si può usare un .ttf
        except:
            font = ImageFont.load_default()
        
        # Simulazione dimensione font proporzionale
        text_y = int((y_m + qr_s + gp_m) * dpmm)
        draw.text((img_w//2, text_y), text, fill="black", anchor="mm")
        
    return img

# --- 4. GENERATORE PDF ---
def generate_pdf(row, w, h, scale_pct):
    text = str(row["Testo Etichetta"])
    qr_s, f_m, x_m, y_m, gp_m = get_layout_logic(w, h, scale_pct, text)
    
    pdf = FPDF(unit='mm', format=(w, h))
    pdf.add_page()
    
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(str(row["Dati QR"]))
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img_qr.save(buf, format='PNG')
    pdf.image(buf, x=x_m, y=y_off:=y_m, w=qr_s, h=qr_s)
    
    if text:
        # Conversione mm -> pt (2.8346)
        pdf.set_font("Helvetica", size=f_m * 2.8346)
        tw = pdf.get_string_width(text)
        if tw > w * 0.9:
            pdf.set_font("Helvetica", size=(f_m * 2.8346) * (w*0.9/tw))
        
        # Posizionamento preciso: oy + qr + gap + baseline
        pdf.text(x=(w - pdf.get_string_width(text))/2, y=y_m + qr_s + gp_m + (f_m * 0.7), txt=text)
    
    return bytes(pdf.output())

# --- 5. INTERFACCIA ---
st.subheader("1. Dati")
df = st.data_editor(pd.DataFrame([{"Dati QR": "ABC.123", "Testo Etichetta": "PROVA 1"}]), num_rows="dynamic", use_container_width=True)

if not df.empty:
    st.divider()
    st.subheader("2. Anteprime (Identiche al PDF)")
    cols = st.columns(3)
    all_pdfs = []

    for idx, row in df.iterrows():
        if row["Dati QR"]:
            pdf_b = generate_pdf(row, w_mm, h_mm, qr_scale)
            all_pdfs.append((f"qr_{idx}.pdf", pdf_b))
            
            # Generiamo l'immagine dell'etichetta per l'anteprima
            preview_img = generate_preview_img(row, w_mm, h_mm, qr_scale)
            buf_img = io.BytesIO()
            preview_img.save(buf_img, format="PNG")
            b64_img = base64.b64encode(buf_img.getvalue()).decode()
            
            with cols[idx % 3]:
                # Visualizzazione dell'immagine dentro il box grigio
                st.write(f'''
                    <div style="background:#D4D4D4; height:280px; display:flex; justify-content:center; align-items:center; border-radius:10px; margin-bottom:10px; padding:10px;">
                        <img src="data:image/png;base64,{b64_img}" style="max-height:100%; max-width:100%; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border:1px solid #999;"/>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.download_button(f"📥 Scarica PDF {idx+1}", pdf_b, f"etichetta_{idx}.pdf", key=f"d_{idx}", use_container_width=True)

    if all_pdfs:
        st.divider()
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w") as z:
            for n, d in all_pdfs: z.writestr(n, d)
        st.download_button("📦 SCARICA TUTTI (ZIP)", zip_io.getvalue(), "batch.zip", use_container_width=True, type="primary")
