import cv2
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import requests
from io import BytesIO  # Import BytesIO

def apply_watershed(img_bgr):
    # Làm mờ và chuyển đổi sang ảnh xám
    blurred = cv2.medianBlur(img_bgr, ksize=3)
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

    # Binarization
    _, image_thres = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Tạo mask cho Watershed
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(
        image_thres, cv2.MORPH_OPEN, kernel=kernel, iterations=2)

    # Distance Transform
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)

    # Show Sure Foreground
    _, sure_foreground = cv2.threshold(
        src=dist_transform, thresh=0.07*np.max(dist_transform), maxval=255, type=0)

    # Show Sure BackGround
    sure_background = cv2.dilate(
        src=opening, kernel=kernel, iterations=2)

    # change its format to int
    sure_foreground = np.uint8(sure_foreground)

    # Show Unknow
    unknown = cv2.subtract(sure_background, sure_foreground)

    # Gắn nhãn markers
    ret, marker = cv2.connectedComponents(sure_foreground)
    marker = marker + 1
    marker[unknown == 255] = 0

    # Áp dụng Watershed transform
    marker = cv2.watershed(image=img_bgr, markers=marker)

    # Hiển thị Watershed kết quả
    watershed_image = img_bgr.copy()
    watershed_image[marker == -1] = [0, 0, 255]  # Đánh dấu biên giới

    # Segmented Objects
    contour, hierarchy = cv2.findContours(
        image=marker.copy(), mode=cv2.RETR_CCOMP, method=cv2.CHAIN_APPROX_SIMPLE)

    image_vis = img_bgr.copy()

    for contours in contour:
        x, y, w, h = cv2.boundingRect(contours)
        if h > 47 and w > 40 and h < 193 and w < 165:
            cv2.rectangle(image_vis, (x, y),
                          (x + w, y + h), (0, 255, 0), 1)

    # Trả về ảnh kết quả
    return img_bgr, blurred, image_thres, opening, dist_transform, sure_foreground, sure_background, unknown, marker, watershed_image, image_vis