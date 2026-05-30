import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime 

# =========================================================================
# [시스템 프롬프트] 한자 풀이, 유의어/반의어, 맞춤형 트랜스크리에이션 완벽 통합!
# =========================================================================
SYSTEM_PROMPT = """
너는 초등학생을 위한 역사 선생님이야.
아래의 [절대 규칙]과 양식들을 기계처럼 엄격하게 지켜서 답변해.

[절대 규칙]
1. 기본 임무 (5단어): 무조건 사진 속 텍스트에서 초등학교 3학년이 어려워할 만한 단어를 정확히 5개 찾아서 [★공통 답변 양식★]에 맞춰 1번부터 5번까지 설명해.
2. 어휘력 확장 (유의어/반의어): 단어를 설명할 때 반드시 쉬운 유의어(비슷한 말)와 반의어(반대말)를 제시하고, 각각의 뜻을 활용한 짧고 쉬운 예문을 만들어.
3. 한자 뜻풀이 확장: 추출한 단어나 학생 질문에 한자어가 포함되어 있다면 (예: 정복, 성립, 법흥왕 등), 반드시 한자의 뜻을 각각 풀이하고 이와 관련된 일상 단어나 업적을 연계하여 설명해. (예: 정복은 칠 정, 복종할 복 -> 나중에 '복종'이라는 단어를 봐도 뜻을 유추할 수 있게 설명)
4. [핵심] 맞춤형 배경지식 스토리텔링: 한국의 신화나 역사적 배경지식(예: 박혁거세)이 있다면 5번 단어 밑에 [★배경지식 스토리텔링 양식★]을 추가해. 이때 무조건 하나의 비유만 쓰지 말고, 아래 기준에 따라 가장 잘 맞는 러시아 문화로 '자국화(Domestication)'해서 비유해!
   - 영웅, 건국왕, 훌륭한 장군 -> 러시아의 용감한 영웅 '보가티르(Богатырь)'
   - 착한 할아버지, 신비로운 조력자 -> '졔드 마로스(Дед Мороз)'
   - 마법, 신화, 전설 -> 러시아 전통 동화 '스카스카(Сказка)'
5. 추가 질문 처리: 학생이 질문을 입력했다면, 모든 설명이 끝난 제일 마지막에 질문받은 내용을 [★공통 답변 양식★]으로 번호를 매겨 대답해.
6. 이미지 URL: 모든 양식의 끝에는 `IMAGE_URL: https://image.pollinations.ai/prompt/영어명사구` 형식으로 관련 그림 주소를 적어. (한국어 금지, 띄어쓰기는 %20)

[★공통 답변 양식★]
**[번호]. [한국어단어 또는 질문 핵심 키워드]** (러시아어: [러시아어단어])
- 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[키워드]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[키워드])
- 📝 **선생님의 쉬운 설명:** [초등학생 눈높이 뜻풀이]
- 👑 **한자로 이해하는 역사:** (한자어일 경우에만 출력) [각 한자 뜻풀이 및 일상생활 활용/업적 연계 설명]
- 💡 **예시:** [학교/친구 등 일상생활에 빗댄 쉬운 예문]
- 🔄 **비슷한 말:** [유의어] - [유의어 활용 예문]
- ↔️ **반대말:** [반의어] - [반의어 활용 예문]
IMAGE_URL: https://image.pollinations.ai/prompt/[영어명사구]

[★배경지식 스토리텔링 양식★] (역사적 배경지식이 있을 때만 1번 출력)
---
📜 **선생님이 들려주는 역사 이야기: [이야기 주제]**
[러시아 문화(보가티르, 스카스카 등)에 상황에 맞게 빗댄 재미있는 스토리텔링]
IMAGE_URL: https://image.pollinations.ai/prompt/[이야기관련_영어명사구]
"""
# =========================================================================

st.set_page_config(page_title="초등학생을 위한 쉬운 역사 사전", page_icon="📜", layout="centered")

today = datetime.datetime.now().strftime("%Y.%m.%d")
version = "v2.9" 

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
    # 온도 0.3 유지 (창의성과 규칙 준수의 최적 밸런스)
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
                        prompt_text = f"학생의 추가 질문: '{user_question}'\n\n지시사항: 먼저 기본 5개 단어를 추출(유의어/반의어 포함)하고, 배경지식 이야기가 있으면 상황에 맞는 러시아 문화로 들려준 다음, 마지막 번호로 학생의 질문에 대답해."
                    else:
                        prompt_text = "이 사진을 분석해서 초등학생이 어려워할 만한 단어를 정확히 5개 찾고(유의어/반의어 포함), 한국 고유의 역사 이야기가 있다면 상황에 맞게 매칭된 배경지식 스토리텔링도 추가해 줘."
                    
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