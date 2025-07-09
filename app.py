import streamlit as st
import requests
from PIL import Image, ImageDraw
import io
import fitz  # PyMuPDF

st.set_page_config(page_title="Clothing Size Detector", layout="centered")
st.title("👕 Clothing Size Recommender")
st.write("Upload or capture a full-body photo (with A4 paper for scale) to detect your height & width.")

# Choose input mode
input_mode = st.radio("Choose Input Method", ["Upload Image/PDF", "Take Live Photo"])
image = None

# Handle image input
if input_mode == "Upload Image/PDF":
    uploaded_file = st.file_uploader("📤 Upload a photo or PDF", type=["jpg", "jpeg", "png", "pdf"])
    if uploaded_file:
        file_type = uploaded_file.type

        try:
            if "pdf" in file_type:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                page = doc.load_page(0)
                pix = page.get_pixmap()
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            else:
                image = Image.open(uploaded_file)
        except Exception as e:
            st.error(f"❌ Could not read the file: {e}")
            image = None

elif input_mode == "Take Live Photo":
    image_data = st.camera_input("📸 Capture using Webcam")
    if image_data:
        image = Image.open(image_data)

# Process image if loaded
if image:
    # Draw guiding rays (vertical & horizontal center lines)
    draw = ImageDraw.Draw(image)
    w, h = image.size
    draw.line([(w//2, 0), (w//2, h)], fill="red", width=2)
    draw.line([(0, h//2), (w, h//2)], fill="red", width=2)

    st.image(image, caption="Input Image (with guide)", use_container_width=True)

    gender = st.radio("Select Gender", ["Male", "Female"])
    product_type = st.selectbox("Select Product Type", ["T-shirt", "Shirt", "Jeans", "Jacket"])

    if st.button("📏 Detect Size"):
        with st.spinner("Detecting..."):
            image_bytes = io.BytesIO()
            image.save(image_bytes, format="JPEG")
            image_bytes = image_bytes.getvalue()

            try:
                response = requests.post(
                    "http://localhost:8000/detect/",
                    files={"file": ("image.jpg", image_bytes, "image/jpeg")}
                )
                result = response.json()
            except Exception as e:
                st.error(f"❌ Backend error: {e}")
                result = {}

            if "height_cm" in result and "width_cm" in result:
                height = result["height_cm"]
                width = result["width_cm"]

                st.success("✅ Detection Successful!")
                st.write(f"🧍 Height: **{height} cm**")
                st.write(f"⬅️➡️ Width: **{width} cm**")

                # Updated size logic (based on width, as per previous request)
                if width <= 28:
                    size = "S"
                elif 28 <= width <= 34:
                    size = "M"
                elif 34 <= width <= 40:
                    size = "L"
                else:
                    size = "XL"

                st.markdown(f"### 🧥 Recommended Size: **{size}**")

                gender_label = "men" if gender == "Male" else "women"
                search_query = f"{gender_label} {product_type.lower()} size {size}"
                amazon_url = f"https://www.amazon.in/s?k={search_query.replace(' ', '+')}"

                st.markdown(f"[🛒 Shop on Amazon for Size {size}]({amazon_url})", unsafe_allow_html=True)

            else:
                st.error("❌ Detection failed. Try again with a clearer full-body photo and A4 reference.")