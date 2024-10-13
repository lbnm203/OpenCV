import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

def grabcut_app(img):
    """
    Hàm thực hiện thuật toán GrabCut trên ảnh.

    Args:
        img (numpy.ndarray): Ảnh đầu vào.

    Returns:
        numpy.ndarray: Ảnh được phân đoạn.
    """
    output = None
    img2 = img.copy()
    mask = np.zeros(img.shape[:2], dtype=np.uint8)

    drawing_mode = st.sidebar.radio(
        "Chọn chế độ vẽ", ["rect"], index=0
    )

    # Thiết lập màu sắc khác nhau cho các chế độ
    if drawing_mode == "rect":
        stroke_color = "#FFFFFF"  # Màu trắng cho 'rect'

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color=stroke_color,
        background_image=Image.fromarray(img),
        update_streamlit=True,
        height=img.shape[0],
        width=img.shape[1],
        drawing_mode=drawing_mode,
        key="canvas",
    )

    if canvas_result.json_data is not None:
        objects = canvas_result.json_data.get("objects", [])
        for obj in objects:
            if obj["type"] == "rect":
                left, top, width, height = map(
                    int, [obj["left"], obj["top"], obj["width"], obj["height"]])
                cv2.rectangle(mask, (left, top),
                              (left + width, top + height), cv2.GC_PR_FGD, -1)
        

    if st.button("Chạy GrabCut để phân đoạn", type="primary"):
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # Sử dụng mask đã được đánh dấu thay vì chỉ sử dụng hình chữ nhật
        cv2.grabCut(img2, mask, None,
                    bgd_model, fgd_model, 10, cv2.GC_INIT_WITH_MASK)

        # Tạo ảnh kết quả
        mask2 = np.where((mask == cv2.GC_FGD) | (
            mask == cv2.GC_PR_FGD), 1, 0).astype('uint8')
        output = img * mask2[:, :, np.newaxis]

        # Hiển thị kết quả
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.image(img, caption='Ảnh đầu vào',
                     use_column_width=True)
        with col2:
            st.image(output, caption='Ảnh được phân đoạn',
                     use_column_width=True)

    return output