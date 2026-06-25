import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime 
import urllib.parse 
import io 

# =========================================================================
# [시스템 프롬프트] 한자 거부감 완화, 설명 5줄 확장, 구글 이미지 연동 적용
# =========================================================================
SYSTEM_PROMPT = """
너는 초등학교 4~6학년이지만, 한국어와 한자가 서툰 '다문화 가정 아이들(1~2학년 수준의 어휘력)'을 가르치는 아주 다정하고 수다스러운 역사 선생님이야.
아래의 [절대 규칙]과 양식들을 기계처럼 엄격하게 지켜서 답변해.

[절대 규칙]
1. 기본 임무: 사진 속 텍스트에서 아이들이 어려워할 만한 단어를 정확히 5개 찾아 [★공통 답변 양식★]에 맞춰 설명해.
2. [강제] 쉬운 설명 5줄 이상: '선생님의 쉬운 설명'은 절대 짧게 쓰지 마! 유치원생에게 동화책을 읽어주듯, 아주 쉬운 일상어만 사용해서 4~5줄 이상으로 길고 풍성하게 풀어서 설명해.
3. [강제] 한자 거부감 없애기: '단어의 숨은 뜻 알아보기' 탭에서는 어려운 한자(예: 征服)를 직접 보여주지 마! 대신 "이 말은 '앞으로 나아가서 적을 엎드리게 만든다'는 뜻이 합쳐진 재미있는 말이야~"처럼 한자어의 원리를 줄글로 부드럽고 재미있게 옛날이야기하듯 풀어서 2~3줄로 설명해.
4. 유의어/반의어 한자 금지: 유의어와 반의어에는 절대 한자 설명을 넣지 마. 오직 1줄짜리 아주 쉬운 뜻풀이와 예문만 넣어.
5. 검색 키워드: 모든 양식의 끝에는 그림을 대신할 구글 검색용 키워드를 `SEARCH_KEYWORD: 한국어명사` 형식으로 적어. (예: SEARCH_KEYWORD: 박혁거세)

[★공통 답변 양식★]
**[번호]. [한국어단어 또는 질문 핵심 키워드]** (러시아어: [러시아어단어])
- 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[키워드]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[키워드])
- 📝 **선생님의 쉬운 설명:** [아주 쉬운 말로 4~5줄 이상 풍성하고 친절하게 줄글로 설명]
- 👑 **단어의 숨은 뜻 알아보기:** (한자어/인물일 경우 출력) [어려운 한자를 빼고, 단어가 만들어진 원리나 업적을 옛날이야기하듯 줄글로 2~3줄 쉽게 설명]
- 💡 **예시:** [학교/친구 등 아이들 일상생활에 빗댄 쉬운 예문]
- 🔄 **비슷한 말:** **[유의어]**
  * 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[유의어]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[유의어])
  * 📝 **뜻:** [한자 설명 없이, 1줄짜리 아주 쉬운 뜻풀이]
  * 💡 **예시:** [유의어 활용 예문]
- ↔️ **반대말:** **[반의어]**
  * 🔗 [📖 국어사전](https://ko.dict.naver.com/#/search?query=[반의어]) | [🇷🇺 한-러 사전](https://dict.naver.com/rukodict/#/search?query=[반의어])
  * 📝 **뜻:** [한자 설명 없이, 1줄짜리 아주 쉬운 뜻풀이]
  * 💡 **예시:** [반의어 활용 예문]
SEARCH_KEYWORD: [구글에 검색할 정확한 한국어 역사 명사]

[★배경지식 스토리텔링 양식★] (역사적 배경지식이 있을 때만 5번 단어 밑에 1번 출력)
---
📜 **선생님이 들려주는 역사 이야기: [이야기 주제]**
[러시아 문화(보가티르, 스카스카 등)에 상황에 맞게 빗댄 재미있는 스토리텔링을 4~5줄로 풍성하게 작성]
SEARCH_KEYWORD: [이야기관련 한국어 명사]
"""
# =========================================================================

st.set_page_config(page_title="초등학생을 위한 쉬운 역사 사전", page_icon="📜", layout="centered")

today = datetime.datetime.now().strftime("%Y.%m.%d")
version = "v3.9 (스트리밍 적용)" 

st.title(f"📜 초등학생을 위한 쉬운 역사 사전 ({version} - {today})")
st.write("선생님에게 교과서 사진을 보여주고 궁금한 걸 물어보세요! 😊")

# API 키 설정 (Secrets 활용)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("앗! 시스템에 API 키가 설정되지 않았습니다. 관리자 페이지(Secrets)를 확인해 주세요.")
    api_key = None

# [핵심 수정] 스트리밍 함수 정의
def get_ai_response_stream(image_bytes, prompt_text, key):
    genai.configure(api_key=key)
    img_for_ai = Image.open(io.BytesIO(image_bytes))
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.3})
    
    # stream=True 를 통해 답변을 조각조각 반환하도록 설정
    response = model.generate_content([SYSTEM_PROMPT, prompt_text, img_for_ai], stream=True)
    return response

uploaded_file = st.file_uploader("1️⃣ 여기에 사진을 드래그하거나 클릭해서 업로드하세요 🖼️", type=["jpg", "jpeg", "png"])
user_question = st.text_input("2️⃣ 특별히 궁금한 게 있나요?", placeholder="질문을 적지 않으면 자동으로 단어 5개를 설명해 줘요!")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="📸 업로드된 교과서 사진", use_container_width=True)
    
    image_bytes_data = uploaded_file.getvalue()

    if st.button("✨ 선생님께 여쭤보기!", type="primary"):
        if api_key:
            # 로딩 메시지를 스피너에서 안내 문구로 변경 (스트리밍 시 스피너가 방해될 수 있음)
            st.info("선생님이 교과서를 꼼꼼히 읽고, 재미있는 이야기를 준비 중이에요! 🕵️‍♂️ (잠시만 기다려주세요...)")
            
            # [핵심 수정] 텍스트가 실시간으로 채워질 빈 공간 생성
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                if user_question:
                    prompt_text = "학생의 추가 질문: '" + user_question + "'\n\n지시사항: 먼저 기본 5개 단어를 추출하고, 배경지식 이야기가 있으면 상황에 맞는 러시아 문화로 들려준 다음, 마지막 번호로 학생의 질문에 대답해."
                else:
                    prompt_text = "이 사진을 분석해서 다문화 아동이 어려워할 만한 단어를 정확히 5개 찾고, 한국 고유의 역사 이야기가 있다면 상황에 맞게 매칭된 배경지식 스토리텔링도 추가해 줘."
                
                # [핵심 수정] 제너레이터를 순회하며 텍스트 갱신
                for chunk in get_ai_response_stream(image_bytes_data, prompt_text, api_key):
                    full_response += chunk.text
                    
                    # 화면 표시용 텍스트 (SEARCH_KEYWORD 태그는 숨김)
                    display_text = ""
                    for line in full_response.split('\n'):
                        if not line.startswith("SEARCH_KEYWORD:"):
                            display_text += line + "\n"
                            
                    # 타이핑 효과를 위한 커서(▌) 추가
                    message_placeholder.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이\n" + display_text + "▌")
                
                # 출력이 끝나면 커서 제거
                message_placeholder.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이\n" + display_text)
                st.success("짜잔! 설명이 완성되었어요! 🎉")
                
                # [핵심 수정] 구글 링크 생성 로직은 스트리밍 완료 후 일괄 처리
                st.markdown("---")
                st.markdown("#### 🖼️ 사진으로 직접 확인해 볼까요?")
                for line in full_response.split('\n'):
                    if line.startswith("SEARCH_KEYWORD:"):
                        keyword = line.replace("SEARCH_KEYWORD:", "").strip()
                        if keyword:
                            encoded_keyword = urllib.parse.quote(keyword)
                            google_url = f"https://www.google.com/search?tbm=isch&q={encoded_keyword}"
                            st.info(f"👉 **['{keyword}' 실제 사진 구글에서 찾아보기 (클릭!)]({google_url})**")
                
            except Exception as e:
                st.error(f"오류가 발생했어요. (에러 내용: {e})")