import cv2 as cv
import numpy as np
import os
import streamlit as st
from PIL import Image
import random
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from sklearn.neighbors import KNeighborsClassifier
import pickle

# Thiết lập cấu hình trang để full width


def load_dataset():
    face = []
    non_face = []
    face_dataset = []

    dir_face = os.listdir('services/Face_Detection/faces_24x24')
    dir_non_face = os.listdir('services/Face_Detection/non_faces_24x24')

    for i in range(100):
        path_face = 'services/Face_Detection/faces_24x24' + dir_face[i]
        path_non = 'services/Face_Detection/non_faces_24x24' + dir_non_face[i]

        image_face = cv.imread(path_face)
        if image_face is not None:
            # image_face = cv.cvtColor(image_face, cv.COLOR_BGR2GRAY)
            face.append(image_face)
        else:
            print(f"Không thể đọc ảnh: {path_face}")

        image_non = cv.imread(path_non)
        if image_non is not None:
            # image_non = cv.cvtColor(image_non, cv.COLOR_BGR2GRAY)
            if len(non_face) < 50:
                non_face.append(image_non)
        else:
            print(f"Không thể đọc ảnh: {path_non}")

    for i in range(len(face)):
        face_dataset.append(face[i])
    for i in range(len(non_face)):
        face_dataset.append(non_face[i])

    labels = np.array([1] * 512 + [0] * 512)
    face_dataset = np.array(face_dataset)

    return face_dataset, labels


def extract_feature_image(img):
    image = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    image = cv.resize(image, (24, 24))
    ii = cv.integral(image)
    val = 0
    for rect in haar_features:
        x, y, w, h, weight = rect
        val += weight * (ii[y + h][x + w] + ii[y][x] -
                         ii[y + h][x] - ii[y][x + w])
    return val


def extract_image_dataset():
    for i in range(len(face_dataset)):
        value = extract_feature_image(face_dataset[i])
        X_train.append(value)


def detect_face_Sub_window(image, model):
    sz = 50
    step = image.shape[0] // 20
    lst_rect = []
    for x in range(0, image.shape[1] - sz, step):
        for y in range(0, image.shape[0] - sz, step):
            sub_window = image[y: y + sz, x: x + sz]
            feature_sub = extract_feature_image(sub_window)
            predictions = model.predict(np.array([[feature_sub]]))
            if predictions[0] == 1:
                lst_rect.append((x, y, sz, sz))
    return lst_rect


def IoU(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    x_max = max(x1, x2)
    x_min = min(x1 + w1, x2 + w2)
    y_max = max(y1, y2)
    y_min = min(y1 + h1, y2 + h2)
    intersect = max(0, x2 - x1) * max(0, y2 - y1)
    area_1 = w1 * h1
    area_2 = w2 * h2
    union_area = area_1 + area_2 - intersect
    return intersect / union_area if union_area != 0 else 0

# Non Maximum Suppression


def NMS(boxes, Iou_threshold):
    choose_boxes = []

    boxes = sorted(boxes, key=lambda box: box[2] * box[3], reverse=True)
    while boxes:
        cur_box = boxes.pop(0)
        choose_boxes.append(cur_box)

        boxes = [box for box in boxes if IoU(cur_box, box) < Iou_threshold]
    return choose_boxes


def IoU_metric(mask_pred, mask_gt):
    # mask_pred = [mask_pred > 0].astype(np.uint8)
    # mask_gt = [mask_gt > 0].astype(np.uint8)

    intersection = np.logical_and(mask_pred, mask_gt).sum()
    union = np.logical_or(mask_pred, mask_gt).sum()
    if union == 0.0:
        return 0.0
    iou = intersection / union
    return iou


def display_sample_images():
    st.title("1. Mô tả tập dữ liệu")

    st.markdown("""## 1.1 Tập dữ liệu Training
                
- 400 ảnh không chứa khuôn mặt

- 400 ảnh chứa khuôn mặt (cả 2 đều được resize về kích thước 24x24)

                """)

    st.markdown("### Một số ảnh minh họa")

    # Đọc một vài ảnh từ folder face
    face_dir = "services/Face_Detection/faces_24x24"
    non_face_dir = "services/Face_Detection/non_faces_24x24"

    face_images = os.listdir(face_dir)
    non_face_images = os.listdir(non_face_dir)

    # Chọn ngẫu nhiên một vài ảnh
    random_face_images = random.sample(face_images, 5)
    random_non_face_images = random.sample(non_face_images, 5)

    # Hiển thị ảnh khuôn mặt
    st.markdown("#### Ảnh Khuôn Mặt")
    cols = st.columns(5)
    for idx, img_name in enumerate(random_face_images):
        img = Image.open(os.path.join(face_dir, img_name))
        cols[idx].image(img, caption=f"{img_name}", use_column_width=True)

    # Hiển thị ảnh không phải khuôn mặt
    st.markdown("#### Ảnh Không Phải Khuôn Mặt")
    cols = st.columns(5)
    for idx, img_name in enumerate(random_non_face_images):
        img = Image.open(os.path.join(non_face_dir, img_name))
        cols[idx].image(img, caption=f"{img_name}", use_column_width=True)


def bbox_to_rect(pos, label):
    img = cv.imread(pos)
    height, width = img.shape[:2]
    with open(label, 'r') as f:
        # convert yolov8 format to x, y, w, h
        for line in f:
            line = line.split()
            x, y, w, h = map(int, line)
            print(x, y, w, h)
            cv.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 4)
    return img


def display_testing():
    st.markdown("## 1.2 Tập dữ liệu Testing")
    test_img_dir = 'services/Face_Detection/'
    imgs = os.listdir(os.path.join(test_img_dir, 'test_image'))
    labels = os.listdir(os.path.join(test_img_dir, 'annotation'))
    imgs.sort()
    labels.sort()

    for i in range(2):
        col = st.columns(5)
        for j in range(5):
            pos = os.path.join(test_img_dir, 'test_image', imgs[i*5+j])
            label = os.path.join(test_img_dir, 'annotation', labels[i*5+j])
            ii = bbox_to_rect(pos, label)
            # resize all ii with same size to display
            ii = cv.resize(ii, (512, 512))
            col[j].image(ii, channels="BGR", use_column_width=True)


def predict():
    st.markdown("### 4. Phát hiện khuôn mặt")
    # st.markdown("#### Chọn ảnh bạn cần phát hiện khuôn mặt")
    image_upload = st.file_uploader(
        "Upload an image", type=["png", "jpg", "jpeg"])
    if image_upload is not None:
        if not os.path.exists('images'):
            os.makedirs('images')
        image = Image.open(image_upload)
        image.save('images/' + image_upload.name)
        img = cv.imread('images/' + image_upload.name)
        img_copy = image.copy()
        st.markdown('Kết quả nhận dạng')
        if img is not None and len(img.shape) == 3:
            faces_rect = detect_face_Sub_window(img, model)
            faces_rect = NMS(faces_rect, float(0.15))
            for (x, y, w, h) in faces_rect:
                img = cv.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            st.image(img, channels="BGR")


def face_detection_app():
    # st.set_page_config(layout='wide')

    st.title('✨ Ứng dụng Face Detection Haar')

    # display_dataset()
    display_sample_images()
    display_testing()

    st.title("2. Quá trình huấn luyện")

    st.markdown(
        """
        ### 2.1 Các tham số huấn luyện
        - numPos: 400 (Số lượng ảnh chứa khuôn mặt)

        - numNeg: 400 (Số lượng ảnh không chứa khuôn mặt)

        - numStage: 15 (Số lượng giai đoạn traning)

        - minHitRate: 0.995 (Tỉ lệ nhận diện đúng mẫu Positive là 99.5{%} cho mỗi giai đoạn).

        - maxFalseAlarmRate: 0.5 (Tỉ lệ nhận diện sai tối đa cho mỗi stage là 50%)

        - width: 24 (Chiều rộng của ảnh)
        
        - height: 24 (Chiều cao của ảnh)
        """
    )

    st.markdown(
        """
        ### 2.2 Huấn luyện KNN

        #### 2.2.1 Các tham số dùng để huấn luyện và độ đo để đánh giá

        -  Tham số k = [1, 2, ..., 50]

        -  Độ đo để đánh giá (IoU):        

        """
    )

    img_iou = cv.imread('assets/IoU.png')
    st.image(img_iou, channels="BGR", width=512)

    st.markdown(
        """
        #### 2.2.2 Biểu đồ Average IoU với tham số k trong KNN
        
        """
    )

    img_avg_iou = cv.imread('assets/result_IoU_haar.png')
    st.image(img_avg_iou, channels="BGR", width=800)

    st.markdown(
        """
        #### - Tham số tốt nhất sau khi huấn luyện

        - ###### Tham số k tốt nhất: 22

        - ###### Average IoU: 0.17
        """
    )

    st.markdown(
        """ 
        ### 3. Kết quả nhận dạng từ tập Testing

        """
    )

    img_results = cv.imread('assets/result_testing_haar.jpg')
    st.image(img_results, channels="BGR", use_column_width=True)

    # st.markdown()
    predict()


cascade_file = 'services/Face_Detection/cascade_output/cascade.xml'
tree = ET.parse(cascade_file)

root = tree.getroot()

rect_feature = []
haar_features = []

for feature in root.findall(".//features/_"):
    for rect in feature.findall(".//rects/_"):
        value = rect.text.strip().split()
        x, y, w, h, weight = map(float, value)
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        haar_features.append((x, y, w, h, weight))


face_dataset, labels = load_dataset()
face_dataset = np.array(face_dataset)
X_train = []


X_train = []
y_train = []
with open('services/Face_Detection/training/X_train.pkl', 'rb') as file:
    X_train = pickle.load(file)

with open('services/Face_Detection/training/y_train.pkl', 'rb') as file:
    y_train = pickle.load(file)

X_train = X_train.reshape(-1, 1)
y_train = y_train.reshape(-1, 1)
y_train = y_train.ravel()
print(X_train.shape, y_train.shape)
model = KNeighborsClassifier(n_neighbors=5)
model.fit(X_train, y_train)
