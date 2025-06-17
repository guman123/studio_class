import streamlit as st
import pandas as pd
from datetime import datetime
from core import load_courses, save_courses, create_course_with_schedule, update_week_info, remove_course

def run_course_week_manager():
    st.header('강의 및 주차 관리')

    tab1, tab2 = st.tabs(["강의 관리", "주차 관리"])

    # ----------------------------- 강의 관리 탭 ----------------------------- #
    with tab1:
        st.subheader("새 강의 추가")

        if 'course_add_success' in st.session_state:
            st.success(st.session_state.pop('course_add_success'))
        if 'course_add_error' in st.session_state:
            st.error(st.session_state.pop('course_add_error'))

        with st.form("add_course_form"):
            new_course = st.text_input("추가할 강의명:")
            start_date = st.date_input("첫 수업 날짜:", datetime.now())
            submit_course = st.form_submit_button("강의 추가")

            if submit_course:
                if not new_course.strip():
                    st.session_state['course_add_error'] = "강의명을 입력해주세요."
                else:
                    start_date_str = start_date.strftime("%Y-%m-%d")
                    if create_course_with_schedule(new_course.strip(), start_date_str):
                        st.cache_data.clear()
                        st.session_state['course_add_success'] = f"'{new_course}' 강의가 15주차로 추가되었습니다."
                    else:
                        st.session_state['course_add_error'] = f"'{new_course}' 강의가 이미 존재하거나 추가할 수 없습니다."
                st.rerun()

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

    # ----------------------------- 주차 관리 탭 ----------------------------- #
    with tab2:
        st.subheader("주차 관리")
        courses = load_courses()

        if courses:
            selected_course = st.selectbox("강의 선택:", list(courses.keys()), key='week_manage_course')
            if selected_course and selected_course in courses:
                weeks = list(courses[selected_course].keys())

                if weeks:
                    st.write(f"**{selected_course}의 주차 목록:**")

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