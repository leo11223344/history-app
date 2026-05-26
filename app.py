import streamlit as st
import google.generativeai as genai
from PIL import Image

# =========================================================================
# [시스템 프롬프트] AI 선생님의 역할과 규칙을 정해주는 가장 중요한 부분!
# 기획자님이 요청하신 규칙을 완벽하게 하드코딩해 두었습니다.
# =========================================================================
SYSTEM_PROMPT = """
너는 다문화 아동(러시아어 문화권 이주배경)을 위한 친절한 역사 선생님이야. 
업로드된 교과서 사진에서 초등학생이 어려워할 만한 한자어(예: 건국, 농경, 상해 등)와 동음이의어(예: 부족)를 3~5개 뽑아내어 설명해.
절대 사전적이고 어려운 직역을 피할 것.
초등학교 2~3학년도 이해할 수 있는 아주 쉬운 일상어(유의어)로 바꿀 것. (예: '상해를 입히다' -> '다른 사람을 다치게 하거나 때리다', '부족' -> '원시 시대에 모여 살던 무리(물 부족 아님!)')
아이들의 이해를 돕기 위해 텍스트 설명과 함께 관련된 직관적인 이모지(Emoji)를 풍부하게 섞어서 출력해 줘.
"""
# =========================================================================

# 1. 웹사이트 기본 설정 (탭 제목, 아이콘 설정)
st.set_page_config(page_title="초등학교 고학년 학생을 위한 쉬운 단어 사전", page_icon="📜", layout="centered")

# 2. 화면 제목 및 설명 꾸미기
st.title("📜 초등학교 고학년 학생을 위한 쉬운 단어 사전")
st.markdown("#### 📸 역사 교과서나 문제집 사진을 올려주세요!")
st.write("어려운 한자어와 헷갈리는 낱말을 초등학교 2~3학년 동생들도 이해할 수 있게 아주 쉽게 풀어서 설명해 줄게요. 선생님이 친절하게 알려줄테니 걱정 마세요! 😊")

# 3. 사이드바(왼쪽 메뉴)에 API 키 입력칸 만들기
with st.sidebar:
    st.header("🔑 AI 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    st.markdown("[무료 API 키 발급받기](https://aistudio.google.com/app/apikey)")
    st.info("여기에 3단계에서 발급받은 긴 코드를 붙여넣으시면 됩니다.")

# 4. 사진 업로드 기능 생성
uploaded_file = st.file_uploader("여기에 사진을 드래그하거나 클릭해서 업로드하세요 🖼️", type=["jpg", "jpeg", "png"])

# 5. 분석 로직 (사진이 업로드 되었을 때만 실행)
if uploaded_file is not None:
    # 업로드한 사진을 화면에 띄워주기
    image = Image.open(uploaded_file)
    st.image(image, caption="📸 업로드된 교과서 사진", use_container_width=True)

    # '분석하기' 버튼
    if st.button("✨ 어려운 역사 단어 쉽게 풀이하기", type="primary"):
        if not api_key:
            st.error("앗! 왼쪽 메뉴에 Gemini API Key를 먼저 입력해 주세요. 😅")
        else:
            with st.spinner("선생님이 사진을 꼼꼼히 읽고 있어요... 잠시만요! 🕵️‍♂️"):
                try:
                    # Gemini API 연결 설정
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # AI에게 규칙과 사진을 함께 던져주고 분석 요청
                    response = model.generate_content([SYSTEM_PROMPT, image])
                    
                    # 결과 화면에 출력
                    st.success("짜잔! 쉬운 설명이 완성되었어요! 🎉")
                    st.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"오류가 발생했어요. API 키가 정확한지 확인해 주세요! (에러 내용: {e})")