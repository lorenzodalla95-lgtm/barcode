import streamlit as st
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="Generator QR & Barcode", layout="centered")

st.title("🔲 Generatore QR & Barcode")
st.write("Crea codici personalizzati pronti per la stampa.")

# --- SIDEBAR DI CONFIGURAZIONE ---
st.sidebar.header("Impostazioni Formato")

# Formati comuni (Larghezza x Altezza in pixel approssimativi a 300 DPI)
formati = {
    "Etichetta Piccola (50x30mm)": (590, 354),
    "Etichetta Media (100x50mm)": (1181, 590),
    "A6 (Cartolina)": (1240, 1748),
    "A5": (1748, 2480),
    "A4": (2480, 3508),
}

formato_scelto = st.sidebar.selectbox("Scegli la dimensione del foglio:", list(formati.keys()))
tipo_codice = st.sidebar.radio("Tipo di codice:", ["QR Code", "Barcode 128"])

st.sidebar.divider()

# --- INPUT DATI ---
col1, col2 = st.columns(2)

with col1:
    data_content = st.text_input("Contenuto del codice (URL/ID):", "123456789")
    
with col2:
    label_text = st.text_input("Testo da visualizzare sotto:", "PRODOTTO ALPHA")

# --- LOGICA DI GENERAZIONE ---
def generate_asset():
    canvas_w, canvas_h = formati[formato_scelto]
    # Creiamo un canvas bianco
    img_final = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(img_final)
    
    try:
        if tipo_codice == "QR Code":
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(data_content)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            
            # Proporzionamento: il QR occupa il 60% della larghezza del foglio
            target_w = int(canvas_w * 0.6)
            qr_img = qr_img.resize((target_w, target_w), Image.Resampling.LANCZOS)
            
            # Posizionamento centrato
            pos_x = (canvas_w - target_w) // 2
            pos_y = (canvas_h - target_w) // 3
            img_final.paste(qr_img, (pos_x, pos_y))
            
            # Aggiunta testo
            text_y = pos_y + target_w + 20

        else:  # Barcode 128
            buffer = io.BytesIO()
            # Generiamo il barcode senza il testo automatico per gestirlo noi
            code = Code128(data_content, writer=ImageWriter())
            code.write(buffer, options={"write_text": False})
            bar_img = Image.open(buffer)
            
            # Proporzionamento: il Barcode occupa l'80% della larghezza
            target_w = int(canvas_w * 0.8)
            aspect_ratio = bar_img.height / bar_img.width
            target_h = int(target_w * aspect_ratio)
            bar_img = bar_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            pos_x = (canvas_w - target_w) // 2
            pos_y = (canvas_h - target_h) // 3
            img_final.paste(bar_img, (pos_x, pos_y))
            
            text_y = pos_y + target_h + 20

        # Scrittura del testo personalizzato
        # Nota: In produzione servirebbe un file .ttf, qui usiamo il font di default
        try:
            font = ImageFont.load_default()
            # Scaliamo il testo in base alla dimensione del foglio
            draw.text(((canvas_w // 2), text_y), label_text, fill="black", font=font, anchor="mm")
        except:
            draw.text((10, text_y), label_text, fill="black")

        return img_final

    except Exception as e:
        st.error(f"Errore nella generazione: {e}")
        return None

# --- VISUALIZZAZIONE E DOWNLOAD ---
if data_content:
    result_img = generate_asset()
    
    if result_img:
        st.image(result_img, caption="Anteprima del formato", use_container_width=True)
        
        # Download button
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.download_button(
            label="Scarica Immagine PNG",
            data=byte_im,
            file_name=f"codice_{formato_scelto.replace(' ', '_')}.png",
            mime="image/png",
        )
