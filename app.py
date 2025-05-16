import streamlit as st
from paddleocr import PaddleOCR
from PIL import Image
from datetime import datetime
import os
import json
import hashlib
import requests

# Hugging Face Zephyr 설정
HF_TOKEN = ""
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def summarize_text_with_zephyr(text):
    prompt = f"다음 글의 핵심을 요약해줘:\\n{text}"
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 300, "temperature": 0.5}}
    response = requests.post(API_URL, headers=headers, json=payload)
    try:
        result = response.json()
        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        else:
            return f"요약 실패: 예상치 못한 응답 형식입니다.\\n{result}"
    except Exception as e:
        return f"요약 실패: {e}\\n\\n응답: {response.text}"

def init_user_data():
    if not os.path.exists('users'):
        os.makedirs('users')
    if not os.path.exists('users/user_data.json'):
        with open('users/user_data.json', 'w', encoding='utf-8') as f:
            json.dump({}, f)

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
    os.makedirs(f'{user_folder}/images', exist_ok=True)
    if not os.path.exists(f'{user_folder}/notes.json'):
        with open(f'{user_folder}/notes.json', 'w', encoding='utf-8') as f:
            json.dump({}, f)

def save_user_note(username, lecture, week, note):
    path = f'users/{username}/notes.json'
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    with open(path, 'r', encoding='utf-8') as f:
        notes = json.load(f)
    notes.setdefault(lecture, {})[week] = note
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=4)

def load_user_notes(username):
    with open(f'users/{username}/notes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 초기화
init_user_data()
ocr = PaddleOCR(lang='korean', use_angle_cls=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = '이미지 업로드'
if 'summary_text' not in st.session_state:
    st.session_state.summary_text = ""
if 'ocr_text' not in st.session_state:
    st.session_state.ocr_text = ""

st.set_page_config(page_title="판서OCR서비스", layout="wide")

def handle_login():
    users = load_users()
    u, p = st.session_state.login_username, st.session_state.login_password
    if u in users and users[u]["password"] == hash_password(p):
        st.session_state.logged_in = True
        st.session_state.username = u
    else:
        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

def handle_signup():
    users = load_users()
    u, p, c = st.session_state.signup_username, st.session_state.signup_password, st.session_state.signup_password_confirm
    if u in users:
        st.error("이미 존재하는 아이디입니다.")
    elif p != c:
        st.error("비밀번호가 일치하지 않습니다.")
    else:
        users[u] = {"password": hash_password(p), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        save_users(users)
        create_user_folder(u)
        st.success("회원가입이 완료되었습니다. 로그인해주세요.")

def handle_logout():
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    st.title("판서OCR서비스 - 로그인")
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    with tab1:
        with st.form("login_form"):
            st.text_input("아이디", key="login_username")
            st.text_input("비밀번호", type="password", key="login_password")
            if st.form_submit_button("로그인"): handle_login()
    with tab2:
        with st.form("signup_form"):
            st.text_input("아이디", key="signup_username")
            st.text_input("비밀번호", type="password", key="signup_password")
            st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
            if st.form_submit_button("회원가입"): handle_signup()
else:
    st.sidebar.write(f"안녕하세요, {st.session_state.username}님!")
    if st.sidebar.button("로그아웃"): handle_logout(); st.experimental_rerun()

    st.sidebar.header('기능 선택')
    col1, col2 = st.sidebar.columns(2)
    if col1.button('이미지 업로드', use_container_width=True):
        st.session_state.menu_selection = '이미지 업로드'
    if col2.button('강의 목록', use_container_width=True):
        st.session_state.menu_selection = '강의 목록'

    if st.session_state.menu_selection == '이미지 업로드':
        st.title('환영합니다! 👋')
        st.markdown('## 강의 사진을 업로드하세요.')
        upload_lecture = st.selectbox('강의 선택:', ['통계학2', '인공지능서비스개발스튜디오', '메타버스와휴먼팩터디자인', 'AI-메타버스사용성평가'])
        lecture_weeks = {
            '통계학2': ['1주차', '2주차', '3주차'],
            '인공지능서비스개발스튜디오': ['1주차', '2주차'],
            '메타버스와휴먼팩터디자인': ['1주차'],
            'AI-메타버스사용성평가': ['1주차']
        }
        upload_week = st.selectbox('주차 선택:', lecture_weeks[upload_lecture])
        img_file = st.file_uploader('', type=['png', 'jpg', 'jpeg'])

        if img_file is not None:
            filename = f"{upload_lecture}_{upload_week}_{datetime.now().isoformat().replace(':', '_')}.jpg"
            user_image_path = f'users/{st.session_state.username}/images'
            os.makedirs(user_image_path, exist_ok=True)
            full_path = os.path.join(user_image_path, filename)

            with open(full_path, 'wb') as f:
                f.write(img_file.getbuffer())
            st.success(f'파일 업로드 성공! {upload_lecture} {upload_week}에 이미지가 저장되었습니다.')
            st.image(Image.open(full_path))

            if st.button("OCR 실행"):
                with st.spinner("OCR 수행 중..."):
                    result = ocr.ocr(full_path)
                    extracted_texts = [line[1][0] for line in result[0]]
                    st.session_state.ocr_text = "\\n".join(extracted_texts)

        note = st.text_area("필기 내용 입력 (OCR 결과 또는 직접 입력):", value=st.session_state.get("ocr_text", ""), height=200)

        if note.strip():
            if st.button("요약하기"):
                with st.spinner("Zephyr 모델로 요약 중..."):
                    st.session_state.summary_text = summarize_text_with_zephyr(note)

        if st.session_state.get("summary_text"):
            st.subheader("요약 내용")
            st.text_area("요약 결과:", value=st.session_state.summary_text, height=150, key="summary_display")

            if st.button("요약 내용을 필기로 저장"):
                save_user_note(st.session_state.username, upload_lecture, upload_week, st.session_state.summary_text)
                st.success("요약 내용이 필기로 저장되었습니다!")

        if st.button("필기 저장"):
            save_user_note(st.session_state.username, upload_lecture, upload_week, note)
            st.success("필기가 저장되었습니다!")

    elif st.session_state.menu_selection == '강의 목록':
        st.sidebar.header('강의 목록')
        lecture_option = st.sidebar.selectbox('강의를 선택하세요:', ['통계학2', '인공지능서비스개발스튜디오', '메타버스와휴먼팩터디자인', 'AI-메타버스사용성평가'])

        lecture_weeks = {
            '통계학2': ['1주차', '2주차', '3주차'],
            '인공지능서비스개발스튜디오': ['1주차', '2주차'],
            '메타버스와휴먼팩터디자인': ['1주차'],
            'AI-메타버스사용성평가': ['1주차']
        }

        selected_week = st.sidebar.selectbox('주차를 선택하세요:', lecture_weeks[lecture_option])
        st.header(f'{lecture_option} - {selected_week}')
        user_image_path = f'users/{st.session_state.username}/images'
        if os.path.exists(user_image_path):
            image_files = [f for f in os.listdir(user_image_path) if f.startswith(f"{lecture_option}_{selected_week}")]
            if image_files:
                latest_image = sorted(image_files)[-1]
                st.image(Image.open(os.path.join(user_image_path, latest_image)), caption=f"최근 이미지: {latest_image}")
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