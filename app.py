import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime 

# =========================================================================
# [시스템 프롬프트] 이미지 에러를 고치고, URL에 영어만 쓰도록 강력 통제했습니다!
# =========================================================================
SYSTEM_PROMPT = """
너는 다문화 아동(특히 러시아어권)을 위한 세상에서 가장 친절한 역사 선생님이야. 

[상황별 대답 규칙]
- 만약 학생이 특별한 질문 없이 사진만 올렸다면: 사진 속에서 초등학생이 어려워할 만한 한자어나 동음이의어(3~5개)를 뽑아서 풀이해 줘.
- 만약 학생이 특정 단어나 배경지식(예: 단군왕검이 누구야?)에 대해 질문했다면: 그 질문에 대한 대답을 '우선적으로' 아주 자세하고 재미있게 설명해 줘.

[엄격한 4대 기본 규칙] (어떤 상황이든 반드시 지킬 것!)
1. 쉬운 풀이와 러시아어 표기:
   - 어려운 단어나 개념은 초등학교 2~3학년 수준의 일상어로 풀어서 설명해.
   - 단어 옆에는 (러시아어: 정확한 사전적 명사 단어)를 표기해 줘.

2. 네이버 사전 링크 2종(국어사전, 한-러 사전) 자동 생성:
   - 설명하는 핵심 한국어 단어 옆에는 무조건 네이버 국어사전과 한-러 사전 하이퍼링크를 나란히 달아줘.
   - 국어사전 링크 양식: `[📖 국어사전](https://ko.dict.naver.com/#/search?query=여기에한국어단어)`
   - 한-러 사전 링크 양식: `[🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=여기에한국어단어)`
   - 출력 예시: `[📖 국어사전](https://ko.dict.naver.com/#/search?query=멸망) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=멸망)`

3. 시각적 이해를 위한 이미지 자동 삽입 (★에러 방지 필수 규칙★):
   - 아이들이 이해하기 쉽도록 설명마다 관련된 이미지를 마크다운으로 무조건 띄워 줘.
   - 양식: `![이미지](https://image.pollinations.ai/prompt/영어로번역된단어)`
   - [가장 중요] URL 주소 안에는 '반드시 영어 단어'만 들어가야 해. (한국어 절대 금지)
   - [가장 중요] 영어 키워드 사이에 절대 빈칸(스페이스)을 넣지 마! 빈칸 대신 반드시 `%20`을 넣어야 해.
   - [가장 중요] URL 끝에 사이즈를 조절하는 특수기호(?width 등)를 절대 붙이지 마!
   - 올바른 예시: `![원시 부족](https://image.pollinations.ai/prompt/primitive%20tribe)`

4. 러시아식 비유 (트랜스크리에이션):
   - 단군왕검, 환웅 같은 한국 고유의 신화/역사는 러시아 아이들에게 친숙한 러시아 문화에 빗대어 설명해 줘.
   - 다정하게 말하고 이모지(Emoji)를 듬뿍 섞어 줘.
"""
# =========================================================================

# 1. 웹사이트 기본 설정 (다문화 아동 -> 초등학생으로 변경)
st.set_page_config(page_title="초등학생을 위한 쉬운 역사 사전", page_icon="📜", layout="centered")

# 2. 오늘 날짜와 버전 세팅
today = datetime.datetime.now().strftime("%Y.%m.%d")
version = "v1.0"

# 3. 타이틀 출력
st.title(f"📜 초등학생을 위한 쉬운 역사 사전 ({version} - {today})")
st.write("선생님에게 교과서 사진을 보여주고 궁금한 걸 물어보세요! 😊")

# 4. 사이드바 AI 설정
with st.sidebar:
    st.header("🔑 AI 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")

# 5. 사진 업로드 및 질문 입력 칸 생성
uploaded_file = st.file_uploader("1️⃣ 여기에 사진을 드래그하거나 클릭해서 업로드하세요 🖼️", type=["jpg", "jpeg", "png"])
user_question = st.text_input("2️⃣ 특별히 궁금한 게 있나요? (예: 단군왕검이 누구야? / 이 단어 뜻이 뭐야?)", placeholder="질문을 적지 않으면, 선생님이 알아서 어려운 단어를 찾아 설명해 줘요!")

# 6. 분석 로직
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="📸 업로드된 교과서 사진", use_container_width=True)

    if st.button("✨ 선생님께 여쭤보기!", type="primary"):
        if not api_key:
            st.error("앗! 왼쪽 메뉴에 Gemini API Key를 먼저 입력해 주세요. 😅")
        else:
            with st.spinner("선생님이 사진을 보고 재미있는 설명을 준비하고 있어요... 🕵️‍♂️"):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    if user_question: 
                        final_prompt = [SYSTEM_PROMPT, f"학생의 질문: {user_question}\n\n위 질문에 대해 사진을 참고하여 시스템 규칙에 맞게 아주 쉽고 자세히 대답해줘.", image]
                    else: 
                        final_prompt = [SYSTEM_PROMPT, "이 사진을 분석해서 규칙에 따라 초등학생이 어려워할 만한 단어들을 찾아서 설명해줘.", image]

                    response = model.generate_content(final_prompt)
                    
                    st.success("짜잔! 설명이 완성되었어요! 🎉")
                    st.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"오류가 발생했어요. (에러 내용: {e})")