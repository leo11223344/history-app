import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime 

# =========================================================================
# [시스템 프롬프트] 추가 질문에 대해서도 완벽한 퀄리티(사전/이미지)를 보장합니다.
# =========================================================================
SYSTEM_PROMPT = """
너는 초등학생을 위한 역사 선생님이야.
너의 임무는 사진 속 텍스트에서 초등학교 3학년 수준에서 어려울 만한 한자어나 고유명사 '5개'를 찾아 양식에 맞춰 설명하는 거야.

[절대 규칙]
1. 어떤 상황에서도(학생의 추가 질문이 있더라도) 반드시 [단어 1]부터 [단어 5]까지 5개 단어 설명을 먼저 출력해야 해.
2. 단어 설명 양식은 아래 [★5단어 필수 양식★]을 토씨 하나 틀리지 않고 똑같이 복사해서 사용해. 사전 링크는 절대 빼먹지 마.
3. 이미지 URL은 `IMAGE_URL: https://image.pollinations.ai/prompt/영어명사` 형식으로 적어. 영어 명사구(1~3단어)만 쓰고 띄어쓰기는 `%20`으로 해. (예: `IMAGE_URL: https://image.pollinations.ai/prompt/ancient%20tomb`)

[★5단어 필수 양식★] (이 양식을 5번 반복할 것)
**번호. [한국어단어]** (러시아어: [러시아어단어])
- 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[한국어단어]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[한국어단어])
- 📝 **선생님의 쉬운 설명:** [초등학생 눈높이 뜻풀이 및 스토리텔링]
- 💡 **예시:** [학교/친구 등 일상생활에 빗댄 쉬운 예문]
IMAGE_URL: https://image.pollinations.ai/prompt/[영어단어]

[★추가 질문 답변 규칙★] (매우 중요)
만약 학생이 추가 질문을 했다면, 위 5개 단어 설명을 모두 마친 후, 맨 밑에 아래 양식으로 대답해. 추가 질문 답변 역시 사전 링크와 이미지를 절대 누락하지 마!
---
🙋‍♂️ **학생의 질문:** [질문 내용]
**[질문의 핵심 키워드(단어)]** (러시아어: [러시아어단어])
- 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[질문의핵심키워드]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[질문의핵심키워드])
- 📝 **선생님의 답변:** [질문에 대한 아주 쉽고 다정한 설명 및 스토리텔링]
- 💡 **예시:** [이해를 돕는 일상생활 예문]
IMAGE_URL: https://image.pollinations.ai/prompt/[질문관련_영어단어]
"""
# =========================================================================

st.set_page_config(page_title="초등학생을 위한 쉬운 역사 사전", page_icon="📜", layout="centered")

today = datetime.datetime.now().strftime("%Y.%m.%d")
version = "v2.4" 

st.title(f"📜 초등학생을 위한 쉬운 역사 사전 ({version} - {today})")
st.write("선생님에게 교과서 사진을 보여주고 궁금한 걸 물어보세요! 😊")

# API 키 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("앗! 시스템에 API 키가 설정되지 않았습니다. 관리자 페이지(Secrets)를 확인해 주세요.")
    api_key = None

@st.cache_data(show_spinner=False)
def get_ai_response(_image_data, prompt_text, key):
    genai.configure(api_key=key)
    # 온도를 다시 0.3으로 복구하여 창의적인 비유와 스토리텔링을 살림
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.3})
    response = model.generate_content([SYSTEM_PROMPT, prompt_text, _image_data])
    return response.text

uploaded_file = st.file_uploader("1️⃣ 여기에 사진을 드래그하거나 클릭해서 업로드하세요 🖼️", type=["jpg", "jpeg", "png"])
user_question = st.text_input("2️⃣ 특별히 궁금한 게 있나요?", placeholder="질문을 적지 않으면 자동으로 단어 5개를 설명해 줘요!")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="📸 업로드된 교과서 사진", use_container_width=True)

    if st.button("✨ 선생님께 여쭤보기!", type="primary"):
        if api_key:
            with st.spinner("선생님이 교과서를 꼼꼼히 읽고, 재미있는 그림을 그리는 중이에요! 🕵️‍♂️🎨 (처음엔 조금 걸려요!)"):
                try:
                    if user_question:
                        prompt_text = f"학생의 추가 질문: '{user_question}'\n먼저 어려운 단어 5개를 [★5단어 필수 양식★]에 맞춰 설명하고, 그 다음에 학생의 질문에 대답해줘."
                    else:
                        prompt_text = "이 사진을 분석해서 초등학생이 어려워할 만한 단어를 정확히 5개 찾아 [★5단어 필수 양식★]에 맞춰 설명해줘."
                    
                    raw_answer = get_ai_response(image, prompt_text, api_key)
                    
                    st.success("짜잔! 설명이 완성되었어요! 🎉")
                    st.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이")
                    
                    text_buffer = ""
                    for line in raw_answer.split('\n'):
                        if line.startswith("IMAGE_URL:"):
                            if text_buffer.strip():
                                st.markdown(text_buffer)
                                text_buffer = "" 
                            
                            img_url = line.replace("IMAGE_URL:", "").strip()
                            if img_url.startswith("http"):
                                st.image(img_url, use_container_width=True)
                        else:
                            text_buffer += line + "\n"
                    
                    if text_buffer.strip():
                        st.markdown(text_buffer)
                    
                except Exception as e:
                    st.error(f"오류가 발생했어요. (에러 내용: {e})")