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
    data_content = st.text_input("Dati nel codice:", "https://google.com")
with col2:
    label_text = st.text_input("Testo sotto:", "TESTO ESEMPIO")

def generate_asset():
    # 1. Gestione Dimensioni Canvas
    w_base, h_base = formati[formato_scelto]
    if orientamento == "Orizzontale":
        canvas_w, canvas_h = max(w_base, h_base), min(w_base, h_base)
    else:
        canvas_w, canvas_h = min(w_base, h_base), max(w_base, h_base)
        
    img_final = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(img_final)
    
    # Parametri dinamici
    margine = 0.10  # 10% di margine
    font_size_ratio = 0.05  # 5% della lunghezza del foglio
    lato_lungo = max(canvas_w, canvas_h)
    text_size = int(lato_lungo * font_size_ratio)
    padding_text = text_size // 2 # Spazio tra codice e scritta

    try:
        # 2. Generazione Codice
        if tipo_codice == "QR Code":
            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(data_content)
            qr.make(fit=True)
            code_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            
            # Scalatura: deve stare nel 80% della larghezza/altezza (considerando il margine)
            max_size = int(min(canvas_w, canvas_h) * (1 - margine * 2))
            code_img = code_img.resize((max_size, max_size), Image.Resampling.LANCZOS)
        
        else:  # Barcode 128
            buffer = io.BytesIO()
            code = Code128(data_content, writer=ImageWriter())
            code.write(buffer, options={"write_text": False, "quiet_zone": 1})
            code_img = Image.open(buffer).convert('RGB')
            
            # Scalatura: larghezza = 80% del foglio
            target_w = int(canvas_w * (1 - margine * 2))
            ratio = code_img.height / code_img.width
            target_h = int(target_w * ratio)
            code_img = code_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # 3. Calcolo Posizionamento Centrato (Codice + Testo)
        code_w, code_h = code_img.size
        total_content_h = code_h + padding_text + text_size
        
        start_x = (canvas_w - code_w) // 2
        start_y = (canvas_h - total_content_h) // 2
        
        # Incolla codice
        img_final.paste(code_img, (start_x, start_y))
        
        # 4. Scrittura Testo
        try:
            # Carichiamo un font se possibile, altrimenti default
            font = ImageFont.load_default()
            # Nota: load_default() non accetta 'size'. Per font scalabili servirebbe un .ttf
            # Ma usiamo una logica di fallback pulita
        except:
            font = None

        text_y = start_y + code_h + padding_text
        draw.text((canvas_w // 2, text_y), label_text, fill="black", font=font, anchor="mt")

        return img_final

    except Exception as e:
        st.error(f"Errore: {e}")
        return None

# --- OUTPUT ---
if data_content:
    with st.spinner('Generazione in corso...'):
        result = generate_asset()
        if result:
            st.image(result, use_container_width=True)
            
            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("Scarica PNG", buf.getvalue(), "codice.png", "image/png")
