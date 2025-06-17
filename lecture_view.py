import os
from PIL import Image
import streamlit as st
from core import load_courses, load_notes, summarize_text, save_note, ocr

def run_lecture_view():
    courses = load_courses()
    if not courses:
        st.warning("등록된 강의가 없습니다. '강의/주차 관리' 메뉴에서 강의를 추가해주세요.")
        return

    lecture_option = st.sidebar.selectbox('강의를 선택하세요:', list(courses.keys()), key='lecture_list_select')
    weeks = courses[lecture_option]
    week_options = [weeks[w]["display_name"] for w in sorted(weeks.keys(), key=lambda x: int(x.split('주차')[0]))]
    week_map = {weeks[w]["display_name"]: w for w in weeks.keys()}

    selected_week_display = st.sidebar.selectbox('주차를 선택하세요:', week_options, key='week_list_select')
    selected_week = week_map[selected_week_display]

    st.header(f'{lecture_option} - {selected_week_display}')
    week_type = weeks[selected_week]["type"]
    if week_type == "midterm":
        st.info("📝 중간고사 주간입니다.")
    elif week_type == "final":
        st.info("📚 기말고사 주간입니다.")
    elif week_type == "holiday":
        st.warning("🏖️ 휴강 주간입니다.")

    user_image_path = os.path.join('images', lecture_option, selected_week)
    if os.path.exists(user_image_path):
        image_files = [f for f in os.listdir(user_image_path) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
        if image_files:
            sorted_images = sorted(image_files, reverse=True)
            st.subheader("업로드한 강의 이미지")
            cols = st.columns(min(3, len(sorted_images)))
            for i, img_file in enumerate(sorted_images[:9]):
                with cols[i % 3]:
                    img = Image.open(os.path.join(user_image_path, img_file))
                    st.image(img, caption=img_file, use_container_width=True)

            selected_image = sorted_images[0]  # 가장 최신 이미지 기본 선택

            if len(sorted_images) > 9:
                selected_image = st.selectbox("추가 이미지 선택:", sorted_images, key='more_images_select')
                img = Image.open(os.path.join(user_image_path, selected_image))
                st.image(img, caption=selected_image)

            if st.button("선택한 이미지에서 OCR 실행", key='ocr_from_list_btn'):
                with st.spinner("OCR 수행 중..."):
                    result = ocr.ocr(os.path.join(user_image_path, selected_image))
                    if result and result[0]:
                        extracted_texts = [line[1][0] for line in result[0]]
                        st.session_state.ocr_text = "\n".join(extracted_texts)

            if st.session_state.get("ocr_text"):
                st.text_area("OCR 결과:", value=st.session_state.ocr_text, height=200, key='ocr_result_display')
                if st.button("OCR 결과 요약하기", key='summarize_ocr_btn'):
                    with st.spinner("텍스트 요약 중..."):
                        summary = summarize_text(st.session_state.ocr_text)
                        st.session_state.summary_text = summary

            if st.session_state.get("summary_text"):
                st.text_area("요약 결과:", value=st.session_state.summary_text, height=150, key='ocr_summary_display')
                if st.button("요약 내용을 필기로 저장 (강의 목록)", key='save_ocr_summary_note_btn'):
                    save_note(lecture_option, selected_week, st.session_state.summary_text)
                    st.success("요약 내용이 필기로 저장되었습니다!")
        else:
            st.info("업로드된 이미지가 없습니다.")
    else:
        st.info("이미지 폴더가 존재하지 않습니다.")

    notes = load_notes()
    if lecture_option in notes and selected_week in notes[lecture_option]:
        st.subheader("내 필기 노트")
        note_val = notes[lecture_option][selected_week]
        st.text_area("필기 내용:", value=note_val, height=200, key='view_note')

        if st.button("필기 내용 요약하기", key='summarize_note_btn'):
            summary = summarize_text(note_val)
            st.text_area("요약 결과:", value=summary, height=150, key='note_summary_display')

        new_note = st.text_area("필기 수정:", value=note_val, height=200, key="edit_note")
        if st.button("필기 수정 저장", key='save_edited_note_btn'):
            save_note(lecture_option, selected_week, new_note)
            st.success("필기가 수정되었습니다!")
    else:
        st.info("이 강의/주차에 저장된 필기가 없습니다.")
                                            