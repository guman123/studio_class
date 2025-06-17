import streamlit as st
import os
import hashlib
from datetime import datetime
from PIL import Image
from core import load_courses, save_note, summarize_text, ocr

def run_image_upload():
    st.header('강의 사진을 업로드하세요.')

    courses = load_courses()
    if not courses:
        st.warning("등록된 강의가 없습니다. '강의/주차 관리' 메뉴에서 강의를 추가해주세요.")
        return

    upload_lecture = st.selectbox('강의 선택:', list(courses.keys()), key='upload_lecture_select')

    if not courses[upload_lecture]:
        st.warning(f"'{upload_lecture}'에 등록된 주차가 없습니다.")
        return

    weeks = courses[upload_lecture]
    week_options = [weeks[w]["display_name"] for w in sorted(weeks.keys(), key=lambda x: int(x.split('주차')[0]))]
    week_map = {weeks[w]["display_name"]: w for w in weeks.keys()}

    upload_week_display = st.selectbox('주차 선택:', week_options, key='upload_week_select')
    upload_week = week_map[upload_week_display]

    img_files = st.file_uploader(
        '여러 이미지를 선택하세요',
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        key='image_uploader'
    )

    # 이미지 저장 처리
    if img_files:
        uploaded_image_paths = []
        user_image_path = os.path.join('images', upload_lecture, upload_week)
        os.makedirs(user_image_path, exist_ok=True)

        # 기존 저장된 이미지들의 해시 계산
        already_existing_hashes = {
            hashlib.md5(open(os.path.join(user_image_path, f), 'rb').read()).hexdigest()
            for f in os.listdir(user_image_path)
            if f.lower().endswith(('png', 'jpg', 'jpeg'))
        }

        for img_file in img_files:
            file_bytes = img_file.getvalue()
            file_hash = hashlib.md5(file_bytes).hexdigest()

            # 메모리 세션과 디스크 저장 이미지에서 중복 검사
            if file_hash in st.session_state.uploaded_image_hashes or file_hash in already_existing_hashes:
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}_{img_file.name}"
            save_path = os.path.join(user_image_path, filename)

            with open(save_path, 'wb') as f:
                f.write(file_bytes)

            uploaded_image_paths.append(save_path)
            st.session_state.uploaded_image_hashes.add(file_hash)

        if uploaded_image_paths:
            st.session_state.uploaded_image_paths = uploaded_image_paths
            st.success(f"{len(uploaded_image_paths)}개의 새 이미지가 저장되었습니다! {upload_lecture} {upload_week_display}에 저장됨.")
        else:
            st.info("모든 이미지는 이미 업로드된 상태입니다.")

    if st.session_state.uploaded_image_paths:
        st.subheader('업로드한 이미지들')
        cols = st.columns(min(3, len(st.session_state.uploaded_image_paths)))
        for i, img_path in enumerate(st.session_state.uploaded_image_paths):
            with cols[i % 3]:
                img = Image.open(img_path)
                st.image(img, caption=os.path.basename(img_path), use_container_width=True)

        if st.button("OCR 실행", key='ocr_execute_btn'):
            with st.spinner("OCR 수행 중..."):
                all_texts = []
                for img_path in st.session_state.uploaded_image_paths:
                    result = ocr.ocr(img_path)
                    if result and result[0]:
                        extracted_texts = [line[1][0] for line in result[0]]
                        all_texts.extend(extracted_texts)
                st.session_state.ocr_text = "\n".join(all_texts)

            st.session_state.uploaded_image_paths = []
            st.session_state.uploaded_image_hashes = set()

    note = st.text_area(
        "필기 내용 입력 (OCR 결과 또는 직접 입력):",
        value=st.session_state.get("ocr_text", ""),
        height=200,
        key='note_input'
    )

    if note.strip() and st.button("요약하기", key='summarize_btn'):
        with st.spinner("텍스트 요약 중..."):
            st.session_state.summary_text = summarize_text(note)

    if st.session_state.get("summary_text"):
        st.subheader("요약 내용")
        st.text_area("요약 결과:", value=st.session_state.summary_text, height=150, key="summary_display")
        if st.button("요약 내용을 필기로 저장", key='save_summary_btn'):
            save_note(upload_lecture, upload_week, st.session_state.summary_text)
            st.success("요약 내용이 필기로 저장되었습니다!")

    if st.button("필기 저장", key='save_note_btn'):
        save_note(upload_lecture, upload_week, note)
        st.success("필기가 저장되었습니다!")
