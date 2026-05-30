import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime 

# =========================================================================
# [시스템 프롬프트] 안정성과 교육적 효과를 극대화하도록 규칙을 대폭 강화했습니다.
# =========================================================================
SYSTEM_PROMPT = """
너는 초등학생을 위한 세상에서 가장 친절한 역사 선생님이야. 
사진 속 내용을 분석하여 답변할 때, 아래의 [대답 규칙]을 기계처럼 엄격하게 지켜.

[상황별 대답 규칙]
- 학생이 질문 없이 사진만 올렸다면: 사진 속 텍스트를 스캔하여, 초등학교 3학년이 가장 어려워할 만한 한자어나 고유명사를 **정확히 1번부터 5번까지 번호를 매겨서 5개만 추출**해.
- 학생이 특정 질문(예: 단군왕검이 누구야?)을 했다면: 5개 추출을 멈추고, 그 질문에 대해서만 아주 자세하고 재미있게 답변해 줘.

[엄격한 5대 기본 규칙] (어떤 상황이든 반드시 지킬 것!)
1. 쉬운 풀이와 러시아어 표기: 단어 옆에 (러시아어: 러시아어 명사)를 적고, 뜻을 아주 쉽게 설명해 줘.
2. [강제] 생활 밀착형 쉬운 예문: 뜻풀이 아래에 반드시 초등학생의 일상생활(학교, 친구, 가족 등)에 빗댄 쉬운 예시 문장을 1개 이상 만들어 줘. (예: "우리 반 친구들이 체육대회에서 하나의 '부족'처럼 똘똘 뭉쳤어!")
3. 스토리텔링 강화: 박혁거세, 장수왕 등 어려운 고유명사는 단순 설명을 넘어 1~2줄의 웃기거나 흥미로운 이야기로 풀어줘.
4. 네이버 사전 링크 2종: 설명하는 단어 옆에 `[📖 국어사전](https://ko.dict.naver.com/#/search?query=단어) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=단어)` 링크를 꼭 달아줘.
5. [가장 중요] 시각 자료 분리 제출 (이미지 에러 방지 규칙):
   - 설명 내용과 관련된 귀여운 동화책 스타일의 이미지 주소를 만들어야 해.
   - 텍스트 답변이 모두 끝난 후, 맨 마지막 줄에 오직 `IMAGE: https://image.pollinations.ai/prompt/영어로번역된핵심단어` 형식으로 딱 한 줄만 적어줘.
   - URL 주소 안에는 절대 한국어를 쓰지 말고 영어만 써야 하며, 빈칸(스페이스) 대신 반드시 `%20`을 넣어!
   - 예시: IMAGE: https://image.pollinations.ai/prompt/cute%20primitive%20tribe%20illustration
"""
# =========================================================================

# 1. 웹사이트 기본 설정 
st.set_page_config(page_title="초등학생을 위한 쉬운 역사 사전", page_icon="📜", layout="centered")

# 2. 오늘 날짜와 버전 세팅
today = datetime.datetime.now().strftime("%Y.%m.%d")
version = "v2.0" 

# 3. 타이틀 출력
st.title(f"📜 초등학생을 위한 쉬운 역사 사전 ({version} - {today})")
st.write("선생님에게 교과서 사진을 보여주고 궁금한 걸 물어보세요! 😊")

# 4. [핵심] API 키를 화면이 아닌 시스템 뒷단(Secrets)에서 안전하게 불러옵니다.
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("앗! 시스템에 API 키가 설정되지 않았습니다. 관리자 페이지(Secrets)를 확인해 주세요.")
    api_key = None

# 5. [핵심] 캐싱 기능 적용 (로딩 속도 30초 -> 0.1초 단축)
@st.cache_data(show_spinner=False)
def get_ai_response(_image_data, prompt_text, key):
    genai.configure(api_key=key)
    # 온도(temperature)를 0.3으로 설정하여 5개 추출의 정확도를 높이고 창의성도 살림
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.3})
    response = model.generate_content([SYSTEM_PROMPT, prompt_text, _image_data])
    return response.text

# 6. 사진 업로드 및 질문 입력 칸 생성
uploaded_file = st.file_uploader("1️⃣ 여기에 사진을 드래그하거나 클릭해서 업로드하세요 🖼️", type=["jpg", "jpeg", "png"])
user_question = st.text_input("2️⃣ 특별히 궁금한 게 있나요? (예: 단군왕검이 누구야? / 이 단어 뜻이 뭐야?)", placeholder="질문을 적지 않으면, 선생님이 알아서 어려운 단어를 5개 찾아 설명해 줘요!")

# 7. 분석 로직 및 이미지 분리 출력 처리
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="📸 업로드된 교과서 사진", use_container_width=True)

    if st.button("✨ 선생님께 여쭤보기!", type="primary"):
        if api_key:
            # 심리적 지루함을 덜어주는 귀여운 로딩 메시지
            with st.spinner("선생님이 교과서를 꼼꼼히 읽고, 재미있는 그림을 그리는 중이에요! 🕵️‍♂️🎨 (처음엔 조금 걸려요!)"):
                try:
                    # 질문 유무에 따른 프롬프트 분기
                    prompt_text = f"학생의 질문: {user_question}\n\n위 질문에 대해 사진을 참고하여 자세히 대답해줘." if user_question else "이 사진을 분석해서 초등학생이 어려워할 만한 단어를 정확히 5개 찾아 설명해줘."
                    
                    # 캐싱된 함수를 호출하여 AI 답변 받아오기
                    raw_answer = get_ai_response(image, prompt_text, api_key)
                    
                    st.success("짜잔! 설명이 완성되었어요! 🎉")
                    st.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이")
                    
                    # [핵심] 텍스트와 이미지 URL을 분리하여 에러 없이 출력!
                    if "IMAGE:" in raw_answer:
                        parts = raw_answer.split("IMAGE:")
                        # 앞부분은 텍스트로 출력
                        st.write(parts[0].strip()) 
                        
                        # 뒷부분은 이미지 전용 명령어로 출력
                        img_url = parts[1].strip()
                        if img_url.startswith("http"):
                            st.image(img_url, caption="✨ 선생님이 준비한 그림 자료", use_container_width=True)
                    else:
                        st.write(raw_answer)
                    
                except Exception as e:
                    st.error(f"오류가 발생했어요. (에러 내용: {e})")