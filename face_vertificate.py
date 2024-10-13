import streamlit as st
from google.cloud import firestore, storage
import json
import toml
import pandas as pd
from datetime import timedelta
import requests
from PIL import Image
from google.cloud.firestore import FieldFilter as fil
import time

st.set_page_config(page_title="Face Verification",
                   initial_sidebar_state="expanded")
st.title("Face Verification")

tools_key = [
    "display_add",
    "display_edit",
    "display_search",
    "display_delete",
    "display_home",
]


@st.cache_resource(show_spinner=False, ttl=3600)
def connect():
    db = firestore.Client.from_service_account_info(st.secrets["google_cloud"])
    bucket = storage.Client.from_service_account_info(
        st.secrets["google_cloud"]).get_bucket('face-vertificates.appspot.com')
    return db, bucket


db, bucket = connect()


def parse_data(doc: firestore.CollectionReference):
    tb = {
        "masv": [],
        "hoten": [],
        "TheSV": [],
        "ChanDung": [],
        # "checkbox": [],
        "id": []
    }

    for i in doc:
        tb["id"].append(i.id)
        j = i.to_dict()
        # tb["checkbox"].append(False)
        tb["masv"].append(j["masv"])
        tb["hoten"].append(j["hoten"])
        path1 = j["TheSV"].replace("gs://face-vertificates.appspot.com/", "")
        path2 = j["ChanDung"].replace(
            "gs://face-vertificates.appspot.com/", "")

        public_url = bucket.blob(path1).generate_signed_url(
            expiration=timedelta(seconds=3300), method='GET')
        tb["TheSV"].append(public_url)

        public_url = bucket.blob(path2).generate_signed_url(
            expiration=timedelta(seconds=3600), method='GET')
        tb["ChanDung"].append(public_url)

    return pd.DataFrame(tb)


def get_all():
    return parse_data(db.collection('face_vertificate').stream())


def display_table(tb):
    # tb['msv'] = tb['msv'].astype(str)  # Convert masv to string
    return st.data_editor(
        tb,
        column_config={
            # "checkbox": st.column_config.CheckboxColumn('Chọn'),
            "id": None,
            "masv": st.column_config.TextColumn("MaSV"),
            "hoten": st.column_config.TextColumn("HoTen"),
            "TheSV": st.column_config.ImageColumn("TheSV"),
            "ChanDung": st.column_config.ImageColumn("ChanDung"),
            # "id": None,
        },
        use_container_width=True,
        disabled=("masv", "hoten", "TheSV", "ChanDung"),
        # key="table",
        hide_index=True,
    )


# sto_ref =
# st.header("1. Dữ liệu")

# if "df_value" not in st.session_state:
#     st.session_state.df_value = get_all()
#     st.session_state.check_len = 0
#     st.session_state.ctr = 0
#     st.session_state.prev_op = None

# for key in tools_key:
#     if key not in st.session_state:
#         st.session_state[key] = False


# with st.container():
#     selected_tool = st.selectbox(
#         "Chọn chức năng",
#         ("Làm mới", "Tìm kiếm", "Thêm", "Chỉnh sửa", "Xóa"),
#         index=0,
#         key="tool_select"
#     )


def sec1():

    st.title('✨ Face Verification')
    st.header("1. Dữ liệu")

    if "df_value" not in st.session_state:
        st.session_state.df_value = get_all()
        st.session_state.check_len = 0
        st.session_state.ctr = 0
        st.session_state.prev_op = None

    for key in tools_key:
        if key not in st.session_state:
            st.session_state[key] = False

    with st.container():
        selected_tool = st.selectbox(
            "Chọn chức năng",
            ("Làm mới", "Tìm kiếm", "Thêm", "Chỉnh sửa", "Xóa"),
            index=0,
            key="tool_select"
        )
    # Check if any key is True

    def callb(key):
        for k in tools_key:
            if k != key and st.session_state[k]:
                st.session_state[k] = False
        st.session_state[key] = True
        st.session_state.prev_op = key

        if selected_tool == "Làm mới":
            callb("display_home")
        elif selected_tool == "Tìm kiếm":
            callb("display_search")
        elif selected_tool == "Thêm":
            callb("display_add")
        elif selected_tool == "Chỉnh sửa":
            callb("display_edit")
        elif selected_tool == "Xóa":
            callb("display_delete")

    # get_all()

    # 11 for tools form 12 for table
    sec11 = st.container()
    sec12 = st.container()

    with sec12:
        if st.session_state.ctr != 0:
            st.session_state.ctr = 0
            st.session_state.df_value = get_all()
        tb = display_table(st.session_state.df_value)

    if st.session_state.display_add:
        def add():
            st.write("Thêm")
            with sec11:
                with st.form(key="add", clear_on_submit=True):
                    cols = st.columns(2)
                    masv = cols[0].text_input("MaSV")
                    hoten = cols[1].text_input("HoTen")

                    the_sv = cols[0].file_uploader("TheSV")
                    chan_dung = cols[1].file_uploader("ChanDung")
                    col = st.columns([8, 1, 1])
                    col[1] = st.form_submit_button(
                        "Thêm", use_container_width=True)

                    if col[1]:
                        print("HERE")
                        if the_sv and chan_dung and masv and hoten:
                            path1 = f"TheSV/{the_sv.name}"
                            path2 = f"ChanDung/{chan_dung.name}"
                            # print(path1, path2, the_sv.t)

                            bucket.blob(path1).upload_from_file(
                                the_sv, content_type=the_sv.type)
                            bucket.blob(path2).upload_from_file(
                                chan_dung, content_type=chan_dung.type)

                            db.collection('face_vertificate').add({
                                "masv": masv,
                                "hoten": hoten,
                                "TheSV": f"face-vertificates.appspot.com/{path1}",
                                "ChanDung": f"face-vertificates.appspot.com/{path2}",
                            })
                            st.toast("Thêm thành công",
                                     icon=":material/check:")
                            st.session_state.ctr = 1
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.warning("Vui lòng cung cấp đầy đủ thông tin")
        add()
    elif st.session_state.display_edit:
        # Get checked rows
        st.session_state.df_value = tb
        checked = tb[tb["checkbox"]]

        if len(checked) == 0:
            st.warning("Chọn một dòng để chỉnh sửa")
            callb("display_home")
        elif len(checked) > 1:
            callb("display_home")
            st.warning("Chỉ được chọn một dòng để chỉnh sửa")
        else:

            def modify(title, data: pd.Series):
                with sec11:
                    st.write(title)
                    with st.form(key="modify") as modify_form:
                        cols = st.columns(2)
                        masv = cols[0].text_input("MaSV", data.get("masv"))
                        hoten = cols[1].text_input("Name", data.get("hoten"))

                        img = Image.open(requests.get(
                            data.get("TheSV"), stream=True).raw)
                        img2 = Image.open(requests.get(
                            data.get("ChanDung"), stream=True).raw)
                        # resize
                        img.thumbnail((200, 200))
                        img2.thumbnail((200, 200))

                        img_col = st.columns(2)
                        if img:
                            img_col[0].image(img, caption="TheSV")
                        if img2:
                            img_col[1].image(img2, caption="ChanDung")

                        cols = st.columns(2)
                        the_sv = cols[0].file_uploader("TheSV", type=[
                            "jpg", "png", "jpeg"], accept_multiple_files=False, help="Upload an image")
                        chan_dung = cols[1].file_uploader("ChanDung", type=[
                            "jpg", "png", "jpeg"], accept_multiple_files=False, help="Upload an image")
                        col = st.form_submit_button(
                            "Add", use_container_width=True)
                        id = db.collection('face_dataset').where(filter=firestore.FieldFilter("masv", "==", data.get(
                            "masv"))).where(filter=firestore.FieldFilter("hoten", "==", data.get("hoten"))).stream()
                        ii = 0

                        for dat in id:
                            ii = dat.id

                        if col:
                            if the_sv:
                                path1 = f"TheSV/{the_sv.name}"
                                bucket.blob(path1).upload_from_file(
                                    the_sv, content_type=the_sv.type)
                                db.collection('face_vertificate').document(ii).update({
                                    "TheSV": f"face-vertificates.appspot.com/{path1}",
                                })
                            if chan_dung:
                                path2 = f"ChanDung/{
                                    chan_dung.name}"
                                bucket.blob(path2).upload_from_file(
                                    chan_dung, content_type=chan_dung.type)
                                db.collection('face_vertificate').document(ii).update({
                                    "ChanDung": f"face-vertificates.appspot.com/{path2}",
                                })
                            if masv:
                                db.collection('face_vertificate').document(ii).update({
                                    "masv": masv,
                                })
                            if hoten:
                                db.collection('face_vertificate').document(ii).update({
                                    "hoten": hoten,
                                })
                            st.session_state.ctr = 1
                            st.toast("Cập nhật thành công",
                                     icon=":material/check:")
                            callb("display_home")
                            time.sleep(1.5)
                            st.rerun()

            modify("Edit", checked.iloc[0])
    elif st.session_state.display_search:
        def search():
            with sec11:
                with st.form(key="search") as search_form:
                    st.write("Search")
                    masv, hoten = st.columns(2)
                    masv = masv.text_input("MaSV")
                    hoten = hoten.text_input("HoTen")
                    sub = st.form_submit_button(
                        "Search", use_container_width=True)
                    if sub:
                        # like select * from face_dataset where msv like '%msv%' and name like '%name%'
                        maxx = masv + '\uf8ff'
                        maxx2 = hoten + '\uf8ff'
                        dt = db.collection('face_dataset') \
                            .where(filter=fil("masv", ">=", masv)) \
                            .where(filter=fil("masv", "<=", maxx)) \
                            .where(filter=fil("hoten", ">=", hoten)) \
                            .where(filter=fil("hoten", "<=", maxx2)) \
                            .stream()
                        st.session_state.df_value = parse_data(dt)
                        st.session_state.ctr = 0
                        callb("display_home")
                        time.sleep(1.5)
                        st.rerun()

        search()
    elif st.session_state.display_delete:
        def delete(checked: pd.DataFrame):
            for i in checked:
                db.collection('face_vertificate').document(i).delete()
            st.session_state.ctr = 1
            callb("display_home")
            st.toast("Xóa thành công", icon=":material/check:")
            time.sleep(1.5)
            st.rerun()

        checked = tb[tb["checkbox"] == True]["id"].tolist()
        if len(checked) == 0:
            st.warning("Vui lòng chọn ít nhất 1 dòng để xóa")
        else:
            callb("display_home")
            delete(checked)
            callb("display_home")
    elif st.session_state.display_home:
        callb("empty")
        st.cache_data.clear()
        # Reset
        st.session_state.ctr = 1
        st.rerun()


sec1()
