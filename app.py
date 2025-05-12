# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime
import os
import json
import hashlib

# 페이지 설정
st.set_page_config(
    page_title="판서OCR서비스",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 데이터 초기화 함수
def init_user_data():
    if not os.path.exists('users'):
        os.makedirs('users')
    if not os.path.exists('users/user_data.json'):
        with open('users/user_data.json', 'w', encoding='utf-8') as f:
            json.dump({}, f)

# 사용자 정보 관련 함수
def load_users():
    with open('users/user_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open('users/user_data.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_folder(username):
    user_folder = f'users/{username}'
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    for subdir in ['images']:
        path = f'{user_folder}/{subdir}'
        if not os.path.exists(path):
            os.makedirs(path)
    # 노트와 강의 목록 초기화
    if not os.path.exists(f'{user_folder}/notes.json'):
        with open(f'{user_folder}/notes.json', 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not os.path.exists(f'{user_folder}/courses.json'):
        with open(f'{user_folder}/courses.json', 'w', encoding='utf-8') as f:
            json.dump([], f)

# 강의 정보 관련 함수
def get_user_courses(username):
    course_file = f'users/{username}/courses.json'
    if not os.path.exists(course_file):
        with open(course_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(course_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_user_courses(username, courses):
    with open(f'users/{username}/courses.json', 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)

# 노트 관련 함수
def save_user_note(username, lecture, week, note):
    with open(f'users/{username}/notes.json', 'r', encoding='utf-8') as f:
        notes = json.load(f)
    if lecture not in notes:
        notes[lecture] = {}
    notes[lecture][week] = note
    with open(f'users/{username}/notes.json', 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=4)

def load_user_notes(username):
    with open(f'users/{username}/notes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 세션 상태 초기화
init_user_data()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = '이미지 업로드'
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []

# 로그인 함수
def handle_login():
    users = load_users()
    username = st.session_state.login_username
    password = st.session_state.login_password
    if username in users and users[username]["password"] == hash_password(password):
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    else:
        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
        return False

# 회원가입 함수
def handle_signup():
    users = load_users()
    username = st.session_state.signup_username
    password = st.session_state.signup_password
    password_confirm = st.session_state.signup_password_confirm
    if username in users:
        st.error("이미 존재하는 아이디입니다.")
        return False
    if password != password_confirm:
        st.error("비밀번호가 일치하지 않습니다.")
        return False
    users[username] = {
        "password": hash_password(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_users(users)
    create_user_folder(username)
    st.success("회원가입이 완료되었습니다. 로그인해주세요.")
    return True

# 로그아웃 함수
def handle_logout():
    st.session_state.logged_in = False
    st.session_state.username = None

# 로그인 페이지
if not st.session_state.logged_in:
    st.title("판서OCR서비스 - 로그인")
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    with tab1:
        with st.form("login_form"):
            st.text_input("아이디", key="login_username")
            st.text_input("비밀번호", type="password", key="login_password")
            if st.form_submit_button("로그인"):
                handle_login()
    with tab2:
        with st.form("signup_form"):
            st.text_input("아이디", key="signup_username")
            st.text_input("비밀번호", type="password", key="signup_password")
            st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
            if st.form_submit_button("회원가입"):
                handle_signup()

# 로그인 후 메인 앱
else:
    st.sidebar.write(f"안녕하세요, {st.session_state.username}님!")
    if st.sidebar.button("로그아웃"):
        handle_logout()
        st.experimental_rerun()

    # 강의 추가 기능
    st.sidebar.subheader("내 강의 추가")
    new_course = st.sidebar.text_input("강의명 입력")
    if st.sidebar.button("강의 추가") and new_course:
        courses = get_user_courses(st.session_state.username)
        if new_course not in courses:
            courses.append(new_course)
            save_user_courses(st.session_state.username, courses)
            st.success(f"{new_course} 강의가 추가되었습니다!")

    # 사용자 강의 불러오기
    user_courses = get_user_courses(st.session_state.username)
    if not user_courses:
        st.warning("먼저 사이드바에서 강의를 추가해주세요.")
        st.stop()

    st.sidebar.header('기능 선택')
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button('이미지 업로드', use_container_width=True):
            st.session_state.menu_selection = '이미지 업로드'
    with col2:
        if st.button('강의 목록', use_container_width=True):
            st.session_state.menu_selection = '강의 목록'

    if st.session_state.menu_selection == '이미지 업로드':
        st.title('환영합니다! 👋')
        st.markdown('## 강의 사진을 업로드하세요.')

        upload_lecture = st.selectbox('강의 선택:', user_courses)
        upload_week = st.selectbox('주차 선택:', [f'{i}주차' for i in range(1, 16)])

        img_files = st.file_uploader('여러 이미지를 선택하세요', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if img_files:
            uploaded_image_paths = []
            user_image_path = f'users/{st.session_state.username}/images'
            os.makedirs(user_image_path, exist_ok=True)
            for img_file in img_files:
                current_time = datetime.now()
                filename = f"{upload_lecture}_{upload_week}_{current_time.isoformat().replace(':', '_')}_{img_file.name}"
                with open(os.path.join(user_image_path, filename), 'wb') as f:
                    f.write(img_file.getbuffer())
                uploaded_image_paths.append(os.path.join(user_image_path, filename))

            st.success(f'{len(img_files)}개의 파일이 업로드 되었습니다! {upload_lecture} {upload_week}에 이미지가 저장되었습니다.')
            st.subheader('업로드한 이미지들')
            cols = st.columns(min(3, len(uploaded_image_paths)))
            for i, img_path in enumerate(uploaded_image_paths):
                with cols[i % 3]:
                    img = Image.open(img_path)
                    st.image(img, caption=os.path.basename(img_path), use_column_width=True)

            note = st.text_area("필기 내용 입력 (OCR 결과 또는 직접 입력):", height=200)
            if st.button("필기 저장"):
                save_user_note(st.session_state.username, upload_lecture, upload_week, note)
                st.success("필기가 저장되었습니다!")

    else:
        lecture_option = st.sidebar.selectbox('강의를 선택하세요:', user_courses)
        selected_week = st.sidebar.selectbox('주차를 선택하세요:', [f'{i}주차' for i in range(1, 16)])

        st.header(f'{lecture_option} - {selected_week}')
        user_image_path = f'users/{st.session_state.username}/images'
        if os.path.exists(user_image_path):
            image_files = [f for f in os.listdir(user_image_path) if f.startswith(f"{lecture_option}_{selected_week}") and f.lower().endswith(('jpg', 'jpeg', 'png'))]
            if image_files:
                st.subheader("업로드한 강의 이미지")
                sorted_images = sorted(image_files, reverse=True)
                cols = st.columns(min(3, len(sorted_images)))
                for i, img_file in enumerate(sorted_images[:9]):
                    with cols[i % 3]:
                        img = Image.open(os.path.join(user_image_path, img_file))
                        st.image(img, caption=img_file, use_column_width=True)
                if len(sorted_images) > 9:
                    st.subheader("모든 이미지 보기")
                    selected_image = st.selectbox("다른 이미지 선택:", sorted_images)
                    img = Image.open(os.path.join(user_image_path, selected_image))
                    st.image(img, caption=selected_image)

        try:
            user_notes = load_user_notes(st.session_state.username)
            if lecture_option in user_notes and selected_week in user_notes[lecture_option]:
                st.subheader("내 필기 노트")
                st.text_area("필기 내용:", value=user_notes[lecture_option][selected_week], height=200, key="view_note")
                new_note = st.text_area("필기 수정:", value=user_notes[lecture_option][selected_week], height=200, key="edit_note")
                if st.button("필기 수정 저장"):
                    save_user_note(st.session_state.username, lecture_option, selected_week, new_note)
                    st.success("필기가 수정되었습니다!")
            else:
                st.info("이 강의/주차에 저장된 필기가 없습니다.")
        except:
            st.info("이 강의/주차에 저장된 필기가 없습니다.")
