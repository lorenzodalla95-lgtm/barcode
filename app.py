import streamlit as st
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="Generator QR & Barcode PRO", layout="centered")

st.title("🔲 Generatore QR & Barcode")

# --- SIDEBAR ---
st.sidebar.header("Configurazione")
formati = {
    "Etichetta Piccola (50x30mm)": (590, 354),
    "Etichetta Media (100x50mm)": (1181, 590),
    "A6 (Cartolina)": (1240, 1748),
    "A5": (1748, 2480),
    "A4": (2480, 3508),
}

formato_scelto = st.sidebar.selectbox("Dimensione:", list(formati.keys()))
orientamento = st.sidebar.radio("Orientamento:", ["Verticale", "Orizzontale"])
tipo_codice = st.sidebar.radio("Tipo:", ["QR Code", "Barcode 128"])

# --- INPUT ---
col1, col2 = st.columns(2)
with col1:
    data_content = st.text_input("Dati nel codice:", "123456789")
with col2:
    label_text = st.text_input("Testo sotto:", "PRODOTTO ALPHA")

def generate_asset():
    # 1. Dimensioni Canvas
    w_base, h_base = formati[formato_scelto]
    canvas_w, canvas_h = (max(w_base, h_base), min(w_base, h_base)) if orientamento == "Orizzontale" else (min(w_base, h_base), max(w_base, h_base))
        
    img_final = Image.new('RGB', (canvas_w, canvas_h), 'white')
    
    try:
        # 2. Generazione Codice
        if tipo_codice == "QR Code":
            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(data_content)
            qr.make(fit=True)
            code_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            # Margine del 10%
            max_size = int(min(canvas_w, canvas_h) * 0.8) 
            code_img = code_img.resize((max_size, max_size), Image.Resampling.LANCZOS)
        else:
            buffer = io.BytesIO()
            code = Code128(data_content, writer=ImageWriter())
            code.write(buffer, options={"write_text": False, "quiet_zone": 1})
            code_img = Image.open(buffer).convert('RGB')
            target_w = int(canvas_w * 0.8)
            ratio = code_img.height / code_img.width
            code_img = code_img.resize((target_w, int(target_w * ratio)), Image.Resampling.LANCZOS)

        code_w, code_h = code_img.size

        # 3. Creazione del Testo Adattato alla larghezza del codice
        # Creiamo un'immagine temporanea per il testo
        temp_font = ImageFont.load_default()
        # Calcoliamo quanto è lungo il testo con il font di default
        dummy_img = Image.new('RGB', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        bbox = dummy_draw.textbbox((0, 0), label_text, font=temp_font)
        text_w_orig = bbox[2] - bbox[0]
        text_h_orig = bbox[3] - bbox[1]

        # Creiamo l'immagine del testo e la scaliamo alla larghezza del codice
        text_canvas = Image.new('RGB', (text_w_orig, text_h_orig), 'white')
        text_draw = ImageDraw.Draw(text_canvas)
        text_draw.text((0, 0), label_text, fill="black", font=temp_font)
        
        # Scaling del testo: larghezza testo = larghezza codice
        new_text_w = code_w
        new_text_h = int(text_h_orig * (new_text_w / text_w_orig))
        text_img_final = text_canvas.resize((new_text_w, new_text_h), Image.Resampling.LANCZOS)

        # 4. Posizionamento e Centratura
        padding = int(canvas_h * 0.02) # Piccolo spazio tra codice e testo
        total_h = code_h + padding + new_text_h
        
        start_x = (canvas_w - code_w) // 2
        start_y = (canvas_h - total_h) // 2
        
        img_final.paste(code_img, (start_x, start_y))
        img_final.paste(text_img_final, (start_x, start_y + code_h + padding))

        return img_final

    except Exception as e:
        st.error(f"Errore: {e}")
        return None

# --- OUTPUT ---
if data_content:
    result = generate_asset()
    if result:
        st.image(result, use_container_width=True)
        buf = io.BytesIO()
        result.save(buf, format="PNG")
        st.download_button("Scarica PNG", buf.getvalue(), "codice_custom.png", "image/png")
