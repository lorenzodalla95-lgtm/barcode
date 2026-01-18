import streamlit as st
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="Generator QR & Barcode", layout="centered")

st.title("🔲 Generatore QR & Barcode")
st.write("Crea codici personalizzati con orientamento orizzontale o verticale.")

# --- SIDEBAR DI CONFIGURAZIONE ---
st.sidebar.header("Impostazioni Formato")

# Formati comuni (Base x Altezza in pixel a 300 DPI)
formati = {
    "Etichetta Piccola (50x30mm)": (590, 354),
    "Etichetta Media (100x50mm)": (1181, 590),
    "A6 (Cartolina)": (1240, 1748),
    "A5": (1748, 2480),
    "A4": (2480, 3508),
}

formato_scelto = st.sidebar.selectbox("Scegli la dimensione:", list(formati.keys()))

# --- NUOVO SELETTORE ORIENTAMENTO ---
orientamento = st.sidebar.radio("Orientamento pagina:", ["Verticale", "Orizzontale"])

tipo_codice = st.sidebar.radio("Tipo di codice:", ["QR Code", "Barcode 128"])

st.sidebar.divider()

# --- INPUT DATI ---
col1, col2 = st.columns(2)
with col1:
    data_content = st.text_input("Dati nel codice (URL/ID):", "123456789")
with col2:
    label_text = st.text_input("Testo visibile sotto:", "PRODOTTO ALPHA")

# --- LOGICA DI GENERAZIONE ---
def generate_asset():
    # Ottieni dimensioni base
    w, h = formati[formato_scelto]
    
    # Gestione rotazione
    if orientamento == "Orizzontale":
        canvas_w, canvas_h = max(w, h), min(w, h)
    else:
        canvas_w, canvas_h = min(w, h), max(w, h)
        
    img_final = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(img_final)
    
    try:
        if tipo_codice == "QR Code":
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(data_content)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            
            # Proporzionamento (60% della dimensione minore)
            dim_minore = min(canvas_w, canvas_h)
            target_w = int(dim_minore * 0.6)
            qr_img = qr_img.resize((target_w, target_w), Image.Resampling.LANCZOS)
            
            pos_x = (canvas_w - target_w) // 2
            pos_y = (canvas_h - target_w) // 3
            img_final.paste(qr_img, (pos_x, pos_y))
            text_y = pos_y + target_w + (canvas_h * 0.05)

        else:  # Barcode 128
            buffer = io.BytesIO()
            code = Code128(data_content, writer=ImageWriter())
            code.write(buffer, options={"write_text": False})
            bar_img = Image.open(buffer)
            
            # Proporzionamento (80% della larghezza)
            target_w = int(canvas_w * 0.8)
            aspect_ratio = bar_img.height / bar_img.width
            target_h = int(target_w * aspect_ratio)
            bar_img = bar_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            pos_x = (canvas_w - target_w) // 2
            pos_y = (canvas_h - target_h) // 3
            img_final.paste(bar_img, (pos_x, pos_y))
            text_y = pos_y + target_h + (canvas_h * 0.05)

        # Scrittura testo con dimensione dinamica
        font_size = int(canvas_h * 0.05) # Il testo è il 5% dell'altezza della pagina
        try:
            # Nota: Streamlit Cloud potrebbe non avere font TrueType installati. 
            # In tal caso userà il font di default che ignora la dimensione.
            font = ImageFont.load_default()
        except:
            font = None

        draw.text((canvas_w // 2, text_y), label_text, fill="black", font=font, anchor="mm")

        return img_final

    except Exception as e:
        st.error(f"Errore: {e}")
        return None

# --- VISUALIZZAZIONE ---
if data_content:
    result_img = generate_asset()
    if result_img:
        st.image(result_img, caption=f"Anteprima {orientamento}", use_container_width=True)
        
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        st.download_button(
            label="Scarica Immagine PNG",
            data=buf.getvalue(),
            file_name=f"codice_{orientamento.lower()}.png",
            mime="image/png",
        )
