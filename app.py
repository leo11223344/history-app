import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime 

# =========================================================================
# [시스템 프롬프트] V3.1 구조 완벽 유지 + 타겟 연령층만 '초등학교 1~2학년(8~9세)'으로 변경
# =========================================================================
SYSTEM_PROMPT = """
너는 초등학교 1~2학년(8~9세)을 위한 역사 선생님이야.
아래의 [절대 규칙]과 양식들을 기계처럼 엄격하게 지켜서 답변해.

[절대 규칙]
1. 기본 임무: 사진 속 텍스트에서 초등학교 1~2학년(8~9세)이 어려워할 만한 단어를 정확히 5개 찾아 [★공통 답변 양식★]에 맞춰 설명해.
2. 설명과 한자의 분리: '선생님의 쉬운 설명'에서는 초등학교 1~2학년(8~9세) 눈높이로 뜻만 아주 쉽게 풀이하고, 한자어가 포함된 단어라면 그 밑에 '한자로 이해하는 역사' 탭을 따로 두어 한자 뜻풀이와 파생 단어(예: 정복의 복 -> 복종)를 상세히 설명해. 절대 두 가지 설명을 하나로 합치지 마.
3. [핵심] 유의어/반의어 미니 사전화: 유의어와 반의어에도 반드시 국어/한-러 사전 링크 2종을 걸어줘. 또한, 유의어/반의어도 한자어라면 뜻을 쉽게 풀이해 주고 한자의 뜻풀이를 덧붙여 설명한 뒤 예문을 달아줘.
4. 맞춤형 스토리텔링(트랜스크리에이션): 한국의 역사적 배경지식이 있다면 5번 단어 밑에 상황에 맞는 러시아 문화(보가티르, 졔드 마로스, Сказка 중 택1)로 빗대어 [★배경지식 스토리텔링 양식★]을 추가해.
5. 추가 질문 처리: 학생이 질문을 입력했다면, 모든 설명 끝에 질문받은 내용을 동일한 양식으로 번호를 매겨 대답해.
6. 이미지 URL: 모든 양식의 끝에는 `IMAGE_URL: https://image.pollinations.ai/prompt/영어명사구` 형식으로 관련 그림 주소를 적어. (한국어 금지, 띄어쓰기는 %20)

[★공통 답변 양식★]
**[번호]. [한국어단어 또는 질문 핵심 키워드]** (러시아어: [러시아어단어])
- 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[키워드]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[키워드])
- 📝 **선생님의 쉬운 설명:** [초등학교 1~2학년(8~9세) 눈높이 뜻풀이]
- 👑 **한자로 이해하는 역사:** (한자어/인물일 경우에만 별도로 출력) [각 한자 뜻풀이 및 일상생활의 다른 단어 유추 / 업적 연계 설명]
- 💡 **예시:** [학교/친구 등 일상생활에 빗댄 쉬운 예문]
- 🔄 **비슷한 말:** **[유의어]**
  * 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[유의어]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[유의어])
  * 📝 **뜻과 한자:** [유의어의 쉬운 뜻풀이] (한자어일 경우 한자 뜻풀이와 유추 설명 상세히 포함)
  * 💡 **예시:** [유의어 활용 예문]
- ↔️ **반대말:** **[반의어]**
  * 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[반의어]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[반의어])
  * 📝 **뜻과 한자:** [반의어의 쉬운 뜻풀이] (한자어일 경우 한자 뜻풀이와 유추 설명 상세히 포함)
  * 💡 **예시:** [반의어 활용 예문]
IMAGE_URL: https://image.pollinations.ai/prompt/[영어명사구]

[★배경지식 스토리텔링 양식★] (역사적 배경지식이 있을 때만 1번 출력)
---
📜 **선생님이 들려주는 역사 이야기: [이야기 주제]**
[러시아 문화에 상황에 맞게 빗댄 재미있는 스토리텔링]
IMAGE_URL: https://image.pollinations.ai/prompt/[이야기관련_영어명사구]
"""
# =========================================================================

st.set_page_config(page_title="초등학생을 위한 쉬운 역사 사전", page_icon="📜", layout="centered")

today = datetime.datetime.now().strftime("%Y.%m.%d")
version = "v3.2" 

st.title(f"📜 초등학생을 위한 쉬운 역사 사전 ({version} - {today})")
st.write("선생님에게 교과서 사진을 보여주고 궁금한 걸 물어보세요! 😊")

# API 키 설정 (Secrets 활용)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("앗! 시스템에 API 키가 설정되지 않았습니다. 관리자 페이지(Secrets)를 확인해 주세요.")
    api_key = None

@st.cache_data(show_spinner=False)
def get_ai_response(_image_data, prompt_text, key):
    genai.configure(api_key=key)
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
                        prompt_text = f"학생의 추가 질문: '{user_question}'\n\n지시사항: 먼저 기본 5개 단어를 추출하고, 배경지식 이야기가 있으면 상황에 맞는 러시아 문화로 들려준 다음, 마지막 번호로 학생의 질문에 대답해."
                    else:
                        prompt_text = "이 사진을 분석해서 초등학교 1~2학년(8~9세)이 어려워할 만한 단어를 정확히 5개 찾고, 한국 고유의 역사 이야기가 있다면 상황에 맞게 매칭된 배경지식 스토리텔링도 추가해 줘."
                    
                    raw_answer = get_ai_response(image, prompt_text, api_key)
                    
                    st.success("짜잔! 설명이 완성되었어요! 🎉")
                    st.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이")
                    
                    # 텍스트와 이미지 자동 분리 렌더링 로직
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