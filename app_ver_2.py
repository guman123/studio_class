import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime, timedelta
import os
import json
import hashlib
import calendar
import requests
from paddleocr import PaddleOCR

# Hugging Face Zephyr 설정
HF_TOKEN = ""  # 실제 사용 시 토큰 입력 필요
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# 페이지 설정
st.set_page_config(
    page_title="판서OCR서비스",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# OCR 초기화 (세션에 캐싱)
@st.cache_resource
def load_ocr():
    return PaddleOCR(lang='korean', use_angle_cls=True)

ocr = load_ocr()

# 요약 함수
@st.cache_data(show_spinner=False)
def summarize_text_with_zephyr(text):
    prompt = f"다음 글의 핵심을 요약해줘:\n{text}"
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 300, "temperature": 0.5}}
    response = requests.post(API_URL, headers=headers, json=payload)
    try:
        result = response.json()
        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        else:
            return f"요약 실패: 예상치 못한 응답 형식입니다.\n{result}"
    except Exception as e:
        return f"요약 실패: {e}\n\n응답: {response.text}"

# 데이터 관리 함수
@st.cache_data(show_spinner=False)
def load_courses():
    if not os.path.exists('courses/courses.json'):
        return {}
    with open('courses/courses.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_courses(courses):
    with open('courses/courses.json', 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)

@st.cache_data(show_spinner=False)
def load_notes():
    if os.path.exists('notes.json'):
        with open('notes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_note(lecture, week, note):
    notes = load_notes()
    if lecture not in notes:
        notes[lecture] = {}
    notes[lecture][week] = note
    with open('notes.json', 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=4)
def create_course_with_schedule(course_name, start_date_str):
    """15주차 강의를 만들고 날짜 정보를 포함합니다."""
    courses = load_courses()
    
    if course_name in courses:
        return False
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        course_schedule = {}
        
        # 15주차 생성
        for i in range(1, 16):
            week_date = start_date + timedelta(days=(i-1)*7)
            week_name = f"{i}주차"
            week_date_str = week_date.strftime("%Y-%m-%d")
            course_schedule[week_name] = {
                "date": week_date_str,
                "display_name": f"{i}주차({week_date.strftime('%m월 %d일')})",
                "type": "regular"  # regular, midterm, final, holiday
            }
        
        courses[course_name] = course_schedule
        save_courses(courses)
        return True
    except Exception as e:
        print(f"Error creating course: {e}")
        return False

def update_week_info(course_name, week_name, date_str=None, week_type=None):
    """주차 정보를 업데이트합니다."""
    courses = load_courses()
    
    if course_name not in courses or week_name not in courses[course_name]:
        return False
    
    try:
        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            courses[course_name][week_name]["date"] = date_str
            courses[course_name][week_name]["display_name"] = f"{week_name}({date_obj.strftime('%m월 %d일')})"
        
        if week_type:
            courses[course_name][week_name]["type"] = week_type
            
            # 특별 주차 표시 업데이트
            if week_type != "regular":
                type_display = {
                    "midterm": "중간고사",
                    "final": "기말고사",
                    "holiday": "휴강"
                }
                display_name = courses[course_name][week_name]["display_name"]
                week_num = week_name.split("주차")[0]
                date_part = display_name.split("(")[1].split(")")[0]
                
                courses[course_name][week_name]["display_name"] = f"{week_num}주차({date_part}) - {type_display.get(week_type, '')}"
        
        save_courses(courses)
        return True
    except Exception as e:
        print(f"Error updating week: {e}")
        return False

def remove_course(course_name):
    courses = load_courses()
    if course_name in courses:
        del courses[course_name]
        save_courses(courses)
        return True
    return False

def save_note(lecture, week, note):
    if os.path.exists('notes.json'):
        with open('notes.json', 'r', encoding='utf-8') as f:
            notes = json.load(f)
    else:
        notes = {}
    
    if lecture not in notes:
        notes[lecture] = {}
    notes[lecture][week] = note
    
    with open('notes.json', 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=4)

def load_notes():
    if os.path.exists('notes.json'):
        with open('notes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 세션 상태 기본값 초기화
if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = '이미지 업로드'
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []
if 'show_course_manager' not in st.session_state:
    st.session_state.show_course_manager = False
if 'ocr_text' not in st.session_state:
    st.session_state.ocr_text = ""
if 'summary_text' not in st.session_state:
    st.session_state.summary_text = ""

st.title("판서OCR서비스")

# 사이드바 구성
st.sidebar.header('기능 선택')

# 버튼으로 메뉴 선택 (key를 추가하여 새로고침 방지)
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button('이미지 업로드', use_container_width=True, key='btn_upload'):
        st.session_state.menu_selection = '이미지 업로드'
        st.session_state.show_course_manager = False
with col2:
    if st.button('강의 목록', use_container_width=True, key='btn_lectures'):
        st.session_state.menu_selection = '강의 목록'
        st.session_state.show_course_manager = False
with col3:
    if st.button('강의/주차 관리', use_container_width=True, key='btn_manage'):
        st.session_state.show_course_manager = True
        st.session_state.menu_selection = '강의/주차 관리'

# 강의/주차 관리 기능
if st.session_state.show_course_manager:
    st.header('강의 및 주차 관리')
    
    # 강의 관리 탭과 주차 관리 탭
    tab1, tab2 = st.tabs(["강의 관리", "주차 관리"])
    
    with tab1:
        st.subheader("새 강의 추가")
        with st.form("add_course_form"):
            new_course = st.text_input("추가할 강의명:")
            start_date = st.date_input("첫 수업 날짜:", datetime.now())
            submit_course = st.form_submit_button("강의 추가")
            
            if submit_course and new_course:
                start_date_str = start_date.strftime("%Y-%m-%d")
                if create_course_with_schedule(new_course, start_date_str):
                    st.success(f"'{new_course}' 강의가 15주차로 추가되었습니다.")
                    st.rerun()
                else:
                    st.error(f"'{new_course}' 강의가 이미 존재하거나 추가할 수 없습니다.")
        
        st.subheader("강의 삭제")
        courses = load_courses()
        if courses:
            course_to_delete = st.selectbox("삭제할 강의 선택:", list(courses.keys()), key='delete_course_select')
            if st.button("강의 삭제", key='delete_course_btn'):
                if remove_course(course_to_delete):
                    st.success(f"'{course_to_delete}' 강의가 삭제되었습니다.")
                    st.rerun()
                else:
                    st.error("강의 삭제에 실패했습니다.")
        else:
            st.info("등록된 강의가 없습니다. 강의를 추가해주세요.")
    
    with tab2:
        st.subheader("주차 관리")
        courses = load_courses()
        
        if courses:
            selected_course = st.selectbox("강의 선택:", list(courses.keys()), key='week_manage_course')
            
            if selected_course and selected_course in courses:
                weeks = list(courses[selected_course].keys())
                
                if weeks:
                    st.write(f"**{selected_course}의 주차 목록:**")
                    
                    # 주차 정보 테이블로 표시
                    week_data = []
                    for week in sorted(weeks, key=lambda x: int(x.split('주차')[0])):
                        week_info = courses[selected_course][week]
                        week_data.append({
                            "주차": week,
                            "날짜": week_info["date"],
                            "표시명": week_info["display_name"],
                            "유형": week_info["type"]
                        })
                    
                    df = pd.DataFrame(week_data)
                    st.dataframe(df)
                    
                    # 주차 정보 수정
                    st.subheader("주차 정보 수정")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_week = st.selectbox("수정할 주차:", weeks, key='edit_week_select')
                    
                    with col2:
                        week_types = {
                            "regular": "일반 수업", 
                            "midterm": "중간고사", 
                            "final": "기말고사", 
                            "holiday": "휴강"
                        }
                        edit_type = st.selectbox(
                            "주차 유형:", 
                            list(week_types.keys()),
                            format_func=lambda x: week_types[x],
                            index=list(week_types.keys()).index(courses[selected_course][edit_week]["type"]),
                            key='edit_week_type'
                        )
                    
                    # 날짜 형식 변환
                    current_date = datetime.strptime(courses[selected_course][edit_week]["date"], "%Y-%m-%d").date()
                    edit_date = st.date_input("날짜 수정:", current_date, key='edit_week_date')
                    
                    if st.button("주차 정보 수정", key='update_week_btn'):
                        if update_week_info(selected_course, edit_week, edit_date.strftime("%Y-%m-%d"), edit_type):
                            st.success(f"'{edit_week}' 정보가 수정되었습니다.")
                            st.rerun()
                        else:
                            st.error("주차 정보 수정에 실패했습니다.")
                else:
                    st.info(f"{selected_course}에 등록된 주차가 없습니다.")
        else:
            st.info("등록된 강의가 없습니다. 강의를 추가해주세요.")

# 이미지 업로드 메뉴
elif st.session_state.menu_selection == '이미지 업로드':
    # 제목과 소개
    st.header('강의 사진을 업로드하세요.')
    
    # 강의와 주차 선택 (업로드 시)
    courses = load_courses()
    
    if not courses:
        st.warning("등록된 강의가 없습니다. '강의/주차 관리' 메뉴에서 강의를 추가해주세요.")
    else:
        upload_lecture = st.selectbox(
            '강의 선택:',
            list(courses.keys()),
            key='upload_lecture_select'
        )
        
        if not courses[upload_lecture]:
            st.warning(f"'{upload_lecture}'에 등록된 주차가 없습니다.")
        else:
            # 주차 목록 생성 (display_name 표시)
            weeks = courses[upload_lecture]
            week_options = [weeks[w]["display_name"] for w in sorted(weeks.keys(), key=lambda x: int(x.split('주차')[0]))]
            week_map = {weeks[w]["display_name"]: w for w in weeks.keys()}
            
            upload_week_display = st.selectbox(
                '주차 선택:',
                week_options,
                key='upload_week_select'
            )
            
            upload_week = week_map[upload_week_display]
            
            # 여러 이미지 업로드 기능으로 변경
            img_files = st.file_uploader('여러 이미지를 선택하세요', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key='image_uploader')
            
            if img_files:
                uploaded_image_paths = []
                
                user_image_path = 'images'
                if not os.path.exists(user_image_path):
                    os.makedirs(user_image_path)
                
                # 업로드된 각 이미지 처리
                for img_file in img_files:
                    # 이미지명이 고유하도록 시간을 활용하여 변경
                    current_time = datetime.now()
                    filename = f"{upload_lecture}_{upload_week}_{current_time.isoformat().replace(':', '_')}_{img_file.name}"
                    
                    # 폴더에 저장
                    with open(os.path.join(user_image_path, filename), 'wb') as f:
                        f.write(img_file.getbuffer())
                    uploaded_image_paths.append(os.path.join(user_image_path, filename))
                
                st.success(f'{len(img_files)}개의 파일이 업로드 되었습니다! {upload_lecture} {upload_week_display}에 이미지가 저장되었습니다.')
                
                # 업로드된 모든 이미지 표시
                st.subheader('업로드한 이미지들')
                cols = st.columns(min(3, len(uploaded_image_paths)))  # 한 행에 최대 3개의 이미지 표시
                
                for i, img_path in enumerate(uploaded_image_paths):
                    with cols[i % 3]:
                        img = Image.open(img_path)
                        st.image(img, caption=os.path.basename(img_path), use_column_width=True)
                
                # OCR 기능 추가
                if st.button("OCR 실행", key='ocr_execute_btn'):
                    with st.spinner("OCR 수행 중..."):
                        all_texts = []
                        for img_path in uploaded_image_paths:
                            result = ocr.ocr(img_path)
                            if result and result[0]:  # PaddleOCR 결과 확인
                                extracted_texts = [line[1][0] for line in result[0]]
                                all_texts.extend(extracted_texts)
                        
                        st.session_state.ocr_text = "\n".join(all_texts)
            
            # 필기 내용 입력 (OCR 결과 또는 직접 입력)
            note = st.text_area("필기 내용 입력 (OCR 결과 또는 직접 입력):", value=st.session_state.get("ocr_text", ""), height=200, key='note_input')
            
            # 요약 기능 추가
            if note.strip():
                if st.button("요약하기", key='summarize_btn'):
                    with st.spinner("텍스트 요약 중..."):
                        st.session_state.summary_text = summarize_text_with_zephyr(note)
            
            # 요약 결과 표시
            if st.session_state.get("summary_text"):
                st.subheader("요약 내용")
                st.text_area("요약 결과:", value=st.session_state.summary_text, height=150, key="summary_display")
                
                if st.button("요약 내용을 필기로 저장", key='save_summary_btn'):
                    save_note(upload_lecture, upload_week, st.session_state.summary_text)
                    st.success("요약 내용이 필기로 저장되었습니다!")
            
            # 필기 저장
            if st.button("필기 저장", key='save_note_btn'):
                save_note(upload_lecture, upload_week, note)
                st.success("필기가 저장되었습니다!")

# 강의 목록 메뉴
else:  
    st.sidebar.header('강의 목록')
    courses = load_courses()
    
    if not courses:
        st.warning("등록된 강의가 없습니다. '강의/주차 관리' 메뉴에서 강의를 추가해주세요.")
    else:
        lecture_option = st.sidebar.selectbox(
            '강의를 선택하세요:',
            list(courses.keys()),
            key='lecture_list_select'
        )
        
        if not courses[lecture_option]:
            st.warning(f"'{lecture_option}'에 등록된 주차가 없습니다.")
        else:
            # 주차 목록 생성 (display_name 표시)
            weeks = courses[lecture_option]
            week_options = [weeks[w]["display_name"] for w in sorted(weeks.keys(), key=lambda x: int(x.split('주차')[0]))]
            week_map = {weeks[w]["display_name"]: w for w in weeks.keys()}
            
            selected_week_display = st.sidebar.selectbox(
                '주차를 선택하세요:',
                week_options,
                key='week_list_select'
            )
            
            selected_week = week_map[selected_week_display]
            
            # 강의와 주차에 따른 내용 표시
            st.header(f'{lecture_option} - {selected_week_display}')
            
            # 주차 유형에 따른 알림 표시
            week_type = courses[lecture_option][selected_week]["type"]
            if week_type == "midterm":
                st.info("📝 중간고사 주간입니다.")
            elif week_type == "final":
                st.info("📚 기말고사 주간입니다.")
            elif week_type == "holiday":
                st.warning("🏖️ 휴강 주간입니다.")
            
            # 저장된 이미지 확인 및 표시
            user_image_path = 'images'
            if os.path.exists(user_image_path):
                # 해당 강의와 주차에 맞는 이미지 찾기
                image_files = [f for f in os.listdir(user_image_path) 
                           if f.startswith(f"{lecture_option}_{selected_week}") and 
                           (f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png'))]
                
                if image_files:
                    st.subheader("업로드한 강의 이미지")
                    
                    # 이미지 파일을 날짜순으로 정렬
                    sorted_images = sorted(image_files, reverse=True)  # 최신 이미지가 먼저 오도록
                    
                    # 갤러리 형태로 이미지 표시 (그리드 레이아웃)
                    cols = st.columns(min(3, len(sorted_images)))  # 한 행에 최대 3개의 이미지 표시
                    
                    for i, img_file in enumerate(sorted_images[:9]):  # 최대 9개 이미지만 표시
                        with cols[i % 3]:
                            img = Image.open(os.path.join(user_image_path, img_file))
                            st.image(img, caption=img_file, use_column_width=True)
                    
                    # 더 많은 이미지가 있을 경우 선택할 수 있게 함
                    if len(sorted_images) > 9:
                        st.subheader("모든 이미지 보기")
                        selected_image = st.selectbox(
                            "다른 이미지 선택:",
                            sorted_images,
                            key='additional_image_select'
                        )
                        img = Image.open(os.path.join(user_image_path, selected_image))
                        st.image(img, caption=selected_image)
                    
                    # OCR 기능 추가 - 강의 목록에서도 OCR 가능하게
                    if st.button("선택한 이미지에서 OCR 실행", key='ocr_from_list_btn'):
                        if 'selected_image' in locals():
                            with st.spinner("OCR 수행 중..."):
                                img_path = os.path.join(user_image_path, selected_image)
                                result = ocr.ocr(img_path)
                                if result and result[0]:
                                    extracted_texts = [line[1][0] for line in result[0]]
                                    st.session_state.ocr_text = "\n".join(extracted_texts)
                                    st.text_area("OCR 결과:", value=st.session_state.ocr_text, height=200, key='ocr_result_display')
                                    
                                    # 요약 옵션 추가
                                    if st.button("OCR 결과 요약하기", key='summarize_ocr_btn'):
                                        with st.spinner("텍스트 요약 중..."):
                                            summary = summarize_text_with_zephyr(st.session_state.ocr_text)
                                            st.session_state.summary_text = summary
                                            st.text_area("요약 결과:", value=summary, height=150, key='ocr_summary_display')
                        else:
                            st.warning("OCR을 실행할 이미지를 선택해주세요.")
                else:
                    st.info(f"{lecture_option} {selected_week_display}에 업로드된 이미지가 없습니다.")
                            
            # 저장된 노트 불러오기
            try:
                notes = load_notes()
                if lecture_option in notes and selected_week in notes[lecture_option]:
                    st.subheader("내 필기 노트")
                    st.text_area("필기 내용:", value=notes[lecture_option][selected_week], height=200, key="view_note")
                    
                    # 노트 내용 요약 기능
                    if st.button("필기 내용 요약하기", key='summarize_note_btn'):
                        with st.spinner("필기 내용 요약 중..."):
                            summary = summarize_text_with_zephyr(notes[lecture_option][selected_week])
                            st.text_area("요약 결과:", value=summary, height=150, key='note_summary_display')
                    
                    # 수정 가능하도록
                    new_note = st.text_area("필기 수정:", value=notes[lecture_option][selected_week], height=200, key="edit_note")
                    if st.button("필기 수정 저장", key='save_edited_note_btn'):
                        save_note(lecture_option, selected_week, new_note)
                        st.success("필기가 수정되었습니다!")
                else:
                    st.info("이 강의/주차에 저장된 필기가 없습니다.")
            except:
                st.info("이 강의/주차에 저장된 필기가 없습니다.")