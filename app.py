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

# 사용자 데이터 관리 함수
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
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    if not os.path.exists(f'{user_folder}/images'):
        os.makedirs(f'{user_folder}/images')
    if not os.path.exists(f'{user_folder}/notes.json'):
        with open(f'{user_folder}/notes.json', 'w', encoding='utf-8') as f:
            json.dump({}, f)

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

# 초기화
init_user_data()

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = '이미지 업로드'

# 로그인 처리 함수
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

# 회원가입 처리 함수
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

# 로그아웃 처리 함수
def handle_logout():
    st.session_state.logged_in = False
    st.session_state.username = None

# 로그인 화면
if not st.session_state.logged_in:
    st.title("판서OCR서비스 - 로그인")
    
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    
    with tab1:
        with st.form("login_form"):
            st.text_input("아이디", key="login_username")
            st.text_input("비밀번호", type="password", key="login_password")
            submit_login = st.form_submit_button("로그인")
            
            if submit_login:
                handle_login()
    
    with tab2:
        with st.form("signup_form"):
            st.text_input("아이디", key="signup_username")
            st.text_input("비밀번호", type="password", key="signup_password")
            st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
            submit_signup = st.form_submit_button("회원가입")
            
            if submit_signup:
                handle_signup()

else:  # 로그인 상태일 때의 메인 앱
    st.sidebar.write(f"안녕하세요, {st.session_state.username}님!")
    if st.sidebar.button("로그아웃"):
        handle_logout()
        st.experimental_rerun()
    
    # 사이드바 구성
    st.sidebar.header('기능 선택')
    
    # 버튼으로 메뉴 선택
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button('이미지 업로드', use_container_width=True):
            st.session_state.menu_selection = '이미지 업로드'
    with col2:
        if st.button('강의 목록', use_container_width=True):
            st.session_state.menu_selection = '강의 목록'
    
    # 메뉴 선택에 따른 처리
    if st.session_state.menu_selection == '이미지 업로드':
        # 제목과 소개
        st.title('환영합니다! 👋')
        st.markdown('## 강의 사진을 업로드하세요.')
        
        # 강의와 주차 선택 (업로드 시)
        upload_lecture = st.selectbox(
            '강의 선택:',
            ['통계학2', '인공지능서비스개발스튜디오', '메타버스와휴먼팩터디자인', 'AI-메타버스사용성평가']
        )
        
        lecture_weeks = {
            '통계학2': ['1주차', '2주차', '3주차', '4주차', '5주차', '6주차', '7주차', '8주차'],
            '인공지능서비스개발스튜디오': ['1주차', '2주차', '3주차', '4주차'],
            '메타버스와휴먼팩터디자인': ['1주차', '2주차', '3주차'],
            'AI-메타버스사용성평가': ['1주차', '2주차']
        }
        
        upload_week = st.selectbox(
            '주차 선택:',
            lecture_weeks[upload_lecture]
        )
        
        img_file = st.file_uploader('',type=['png', 'jpg', 'jpeg'])
        
        if img_file is not None:
            # 이미지명이 고유하도록 시간을 활용하여 변경
            current_time = datetime.now()
            filename = f"{upload_lecture}_{upload_week}_{current_time.isoformat().replace(':', '_')}.jpg"
            
            # 사용자 폴더에 저장
            user_image_path = f'users/{st.session_state.username}/images'
            if not os.path.exists(user_image_path):
                os.makedirs(user_image_path)
                
            with open(os.path.join(user_image_path, filename), 'wb') as f:
                f.write(img_file.getbuffer())
            st.success(f'파일 업로드 성공! {upload_lecture} {upload_week}에 이미지가 저장되었습니다.')
            
            # 경로로 이미지 출력
            st.subheader('업로드한 이미지')
            img = Image.open(os.path.join(user_image_path, filename))
            st.image(img)
            
            # 사용자 노트 저장
            note = st.text_area("필기 내용 입력 (OCR 결과 또는 직접 입력):", height=200)
            if st.button("필기 저장"):
                save_user_note(st.session_state.username, upload_lecture, upload_week, note)
                st.success("필기가 저장되었습니다!")
    
    else:  # 강의 목록인 경우
        st.sidebar.header('강의 목록')
        lecture_option = st.sidebar.selectbox(
            '강의를 선택하세요:',
            ['통계학2', '인공지능서비스개발스튜디오', '메타버스와휴먼팩터디자인', 'AI-메타버스사용성평가']
        )
        
        # 강의별 주차 데이터
        lecture_weeks = {
            '통계학2': ['1주차', '2주차', '3주차', '4주차', '5주차', '6주차', '7주차', '8주차'],
            '인공지능서비스개발스튜디오': ['1주차', '2주차', '3주차', '4주차'],
            '메타버스와휴먼팩터디자인': ['1주차', '2주차', '3주차'],
            'AI-메타버스사용성평가': ['1주차', '2주차']
        }
        
        # 주차 선택 드롭다운
        selected_week = st.sidebar.selectbox(
            '주차를 선택하세요:',
            lecture_weeks[lecture_option]
        )
        
        # 강의와 주차에 따른 내용 표시
        st.header(f'{lecture_option} - {selected_week}')
        
        # 저장된 사용자 이미지 확인 및 표시
        user_image_path = f'users/{st.session_state.username}/images'
        if os.path.exists(user_image_path):
            # 해당 강의와 주차에 맞는 이미지 찾기
            image_files = [f for f in os.listdir(user_image_path) 
                       if f.startswith(f"{lecture_option}_{selected_week}") and 
                       (f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png'))]
            
            if image_files:
                st.subheader("업로드한 강의 이미지")
                # 최신 이미지 표시 (또는 모든 이미지 표시)
                latest_image = sorted(image_files)[-1]  # 파일명으로 정렬하면 날짜순으로 정렬됨
                img = Image.open(os.path.join(user_image_path, latest_image))
                st.image(img, caption=f"가장 최근 업로드: {latest_image}")
                
                # 만약 여러 이미지가 있다면 선택할 수 있게 함
                if len(image_files) > 1:
                    st.subheader("모든 이미지")
                    selected_image = st.selectbox(
                        "다른 이미지 보기:",
                        sorted(image_files, reverse=True)
                    )
                    if selected_image != latest_image:
                        img = Image.open(os.path.join(user_image_path, selected_image))
                        st.image(img, caption=selected_image)
                        
        # 저장된 사용자 노트 불러오기
        try:
            user_notes = load_user_notes(st.session_state.username)
            if lecture_option in user_notes and selected_week in user_notes[lecture_option]:
                st.subheader("내 필기 노트")
                st.text_area("필기 내용:", value=user_notes[lecture_option][selected_week], height=200, key="view_note")
                
                # 수정 가능하도록
                new_note = st.text_area("필기 수정:", value=user_notes[lecture_option][selected_week], height=200, key="edit_note")
                if st.button("필기 수정 저장"):
                    save_user_note(st.session_state.username, lecture_option, selected_week, new_note)
                    st.success("필기가 수정되었습니다!")
            else:
                st.info("이 강의/주차에 저장된 필기가 없습니다.")
        except:
            st.info("이 강의/주차에 저장된 필기가 없습니다.")
        
        # 기본 강의 내용 표시 (샘플)
        st.subheader("강의 내용")
        if lecture_option == '통계학2':
            if selected_week == '1주차':
                st.text('이번 강의에서는 디지털 트랜스포메이션(Digital Transformation)이 현대 사회와 산업에 미치는 영향에 대해 다루었다. 디지털 트랜스포메이션은 단순한 기술 도입이 아니라, 조직 문화, 비즈니스 모델, 고객 경험 전반에 걸친 근본적인 변화를 의미한다. 강의에서는 주요 사례로 넷플릭스, 아마존, 우버 등의 기업이 소개되었으며, 이들이 어떻게 데이터 분석, 인공지능(AI), 클라우드 컴퓨팅을 활용하여 시장을 선도했는지 살펴보았다. 마지막으로 디지털 변화에 성공적으로 적응하기 위한 기업과 개인의 전략, 예를 들어 지속적인 학습, 민첩한 조직 운영 등이 강조되었다.')
            elif selected_week == '2주차':
                st.text('2주차에서는 통계적 추론의 기본 개념과 확률 분포에 대해 학습하였다. 표본 분포와 모집단 분포의 관계, 중심극한정리, 표준오차 등의 개념을 배웠으며, 이를 통해 데이터 분석 결과의 신뢰성을 평가하는 방법을 익혔다.')
            else:
                st.text(f'{selected_week} 강의 내용이 준비 중입니다.')