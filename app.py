import streamlit as st
# 반드시 Streamlit의 첫 번째 명령어로 set_page_config 호출
st.set_page_config(
    page_title="SnapNote",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


from image_upload import run_image_upload
from lecture_view import run_lecture_view
from course_week_manager import run_course_week_manager


# 세션 상태 초기화
def initialize_session():
    defaults = {
        'menu_selection': '이미지 업로드',
        'uploaded_images': [],
        'show_course_manager': False,
        'ocr_text': '',
        'summary_text': '',
        'uploaded_image_paths': [],
        'uploaded_image_hashes': set()
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session()

st.title("SnapNote")

# 사이드바 메뉴
st.sidebar.header('기능 선택')
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button('이미지 업로드', use_container_width=True):
        st.session_state.menu_selection = '이미지 업로드'
        st.session_state.show_course_manager = False
with col2:
    if st.button('강의 목록', use_container_width=True):
        st.session_state.menu_selection = '강의 목록'
        st.session_state.show_course_manager = False
with col3:
    if st.button('강의/주차 관리', use_container_width=True):
        st.session_state.menu_selection = '강의/주차 관리'
        st.session_state.show_course_manager = True

# 화면 라우팅
if st.session_state.menu_selection == '이미지 업로드':
    run_image_upload()
elif st.session_state.menu_selection == '강의 목록':
    run_lecture_view()
elif st.session_state.menu_selection == '강의/주차 관리':
    run_course_week_manager()