import streamlit as st

st.set_page_config(page_title="OCR 프로젝트", layout="wide") #centered
st.header('판서 이미지 선택')

uploaded_file = st.file_uploader("변환할 이미지를 선택하세요", type=['png','jpg'])

if uploaded_file is not None:
    st.image(uploaded_file, caption='글씨 이미지', width=400)

st.button("텍스트 변환")


