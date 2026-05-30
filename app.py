import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime 

# =========================================================================
# [시스템 프롬프트] AI가 사전 링크를 절대 빼먹지 못하도록 '출력 양식'을 강제했습니다.
# =========================================================================
SYSTEM_PROMPT = """
너는 초등학생을 위한 세상에서 가장 친절한 역사 선생님이야. 
사진 속 내용을 분석하여 답변할 때, 아래의 규칙과 [★필수 출력 양식★]을 기계처럼 엄격하게 지켜.

[상황별 대답 규칙]
- 학생이 질문 없이 사진만 올렸다면: 사진 속 텍스트를 스캔하여, 초등학교 3학년이 가장 어려워할 만한 한자어나 고유명사를 정확히 5개만 추출해.
- 학생이 특정 질문(예: 단군왕검이 누구야?)을 했다면: 5개 추출을 멈추고, 그 질문에 대해서만 아주 자세하고 재미있게 답변해 줘.

[엄격한 5대 기본 규칙]
1. 쉬운 풀이: 뜻을 초등학생 눈높이로 아주 쉽게 설명해.
2. [강제] 생활 밀착형 쉬운 예문: 초등학생의 일상생활(학교, 친구, 가족 등)에 빗댄 쉬운 예시 문장을 반드시 만들어 줘.
3. 스토리텔링: 어려운 고유명사는 1~2줄의 흥미로운 이야기로 풀어줘.
4. 네이버 사전 링크 2종: 설명하는 단어는 무조건 국어사전과 한-러 사전 링크를 포함해야 해.
5. 시각 자료(이미지 에러 방지 규칙): 텍스트 답변이 모두 끝난 후, 맨 마지막 줄에 오직 `IMAGE: https://image.pollinations.ai/prompt/영어로번역된단어` 형식으로 딱 한 줄만 적어. (한국어 금지, 띄어쓰기는 %20 사용)

[★필수 출력 양식★] - 단어를 설명할 때 반드시 아래의 형식을 복사해서 괄호 안의 빈칸만 채워넣어! (사전 링크 절대 누락 금지)
1. **[한국어단어]** (러시아어: [러시아어단어])
   - 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[한국어단어]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[한국어단어])
   - 📝 **선생님의 쉬운 설명:** [초등학생 눈높이 뜻풀이 및 스토리텔링]
   - 💡 **예시:** [생활 밀착형 쉬운 예문]
"""
# =========================================================================

st.set_page_config(page_title="초등학생을 위한 쉬운 역사 사전", page_icon="📜", layout="centered")

today = datetime.datetime.now().strftime("%Y.%m.%d")
version = "v2.1" # 사전 링크 양식 강제 버전

st.title(f"📜 초등학생을 위한 쉬운 역사 사전 ({version} - {today})")
st.write("선생님에게 교과서 사진을 보여주고 궁금한 걸 물어보세요! 😊")

# API 키 숨기기 (Secrets 활용)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("앗! 시스템에 API 키가 설정되지 않았습니다. 관리자 페이지(Secrets)를 확인해 주세요.")
    api_key = None

# 캐싱 적용 (로딩 0.1초 단축) 및 온도 0.3 세팅
@st.cache_data(show_spinner=False)
def get_ai_response(_image_data, prompt_text, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.3})
    response = model.generate_content([SYSTEM_PROMPT, prompt_text, _image_data])
    return response.text

uploaded_file = st.file_uploader("1️⃣ 여기에 사진을 드래그하거나 클릭해서 업로드하세요 🖼️", type=["jpg", "jpeg", "png"])
user_question = st.text_input("2️⃣ 특별히 궁금한 게 있나요? (예: 단군왕검이 누구야? / 이 단어 뜻이 뭐야?)", placeholder="질문을 적지 않으면, 선생님이 알아서 어려운 단어를 5개 찾아 설명해 줘요!")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="📸 업로드된 교과서 사진", use_container_width=True)

    if st.button("✨ 선생님께 여쭤보기!", type="primary"):
        if api_key:
            with st.spinner("선생님이 교과서를 꼼꼼히 읽고, 재미있는 그림을 그리는 중이에요! 🕵️‍♂️🎨 (처음엔 조금 걸려요!)"):
                try:
                    prompt_text = f"학생의 질문: {user_question}\n\n위 질문에 대해 사진을 참고하여 자세히 대답해줘." if user_question else "이 사진을 분석해서 초등학생이 어려워할 만한 단어를 정확히 5개 찾아 설명해줘."
                    
                    raw_answer = get_ai_response(image, prompt_text, api_key)
                    
                    st.success("짜잔! 설명이 완성되었어요! 🎉")
                    st.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이")
                    
                    # 텍스트와 이미지 URL 분리 출력
                    if "IMAGE:" in raw_answer:
                        parts = raw_answer.split("IMAGE:")
                        st.write(parts[0].strip()) 
                        
                        img_url = parts[1].strip()
                        if img_url.startswith("http"):
                            st.image(img_url, caption="✨ 선생님이 준비한 그림 자료", use_container_width=True)
                    else:
                        st.write(raw_answer)
                    
                except Exception as e:
                    st.error(f"오류가 발생했어요. (에러 내용: {e})")