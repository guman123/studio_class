import os
import json
import torch
from datetime import datetime, timedelta
from paddleocr import PaddleOCR
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_text(text, lecture=None):
    if lecture:
        prompt = f"""이 글은 '{lecture}' 강의의 내용이야 강의 내용을 요약하고 즁요한 부분이나 핵심부분 설명해주는데 줄바꿈이나 오타는 너가 정리해서 부탁할게:\n\n{text}. """
    else:
        prompt = f"""다음 글을 핵심 내용만 요약해주는데 줄바꿈이나 오타는 너가 정리해서 부탁할게:\n\n{text}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "너는 전문적인 학습 도우미야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[요약 실패: {str(e)}]"

@st.cache_resource
def load_ocr():
    return PaddleOCR(lang='korean', use_angle_cls=True, use_gpu=torch.cuda.is_available())

ocr = load_ocr()

@st.cache_data(show_spinner=False)
def load_courses():
    if not os.path.exists('courses/courses.json'):
        return {}
    with open('courses/courses.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_courses(courses):
    os.makedirs('courses', exist_ok=True)
    with open('courses/courses.json', 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)

# @st.cache_data(show_spinner=False)
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
    st.cache_data.clear()  # <== 이 줄 추가

def create_course_with_schedule(course_name, start_date_str):
    courses = load_courses()
    if course_name in courses:
        return False
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        course_schedule = {}
        for i in range(1, 16):
            week_date = start_date + timedelta(days=(i-1)*7)
            week_name = f"{i}주차"
            week_date_str = week_date.strftime("%Y-%m-%d")
            course_schedule[week_name] = {
                "date": week_date_str,
                "display_name": f"{i}주차({week_date.strftime('%m월 %d일')})",
                "type": "regular"
            }
        courses[course_name] = course_schedule
        save_courses(courses)
        return True
    except Exception as e:
        print(f"Error creating course: {e}")
        return False

def update_week_info(course_name, week_name, date_str=None, week_type=None):
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
