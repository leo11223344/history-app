import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime
import urllib.parse
import io

# =========================================================================
# [시스템 프롬프트] v4.0
# - 기존: 한자 거부감 완화, 설명 5줄 확장, 구글 이미지 연동
# - 추가: [절대 규칙 6] 교과서 문장 인용 리마인드(복습)를 '고정 출력'으로 승격
#   (부록1·3 인터뷰: "복습 기능이 그때그때 나올 때도 있고 안 나올 때도 있다.
#    고정값으로 교과서 문장을 인용해서 리마인드 설명을 해줘라" 반영)
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
6. [강제/고정 출력] 교과서 복습 리마인드: 각 단어의 설명 맨 마지막에는 반드시 '📚 **교과서에서 다시 보기:**' 항목을 넣어. 사진 속 교과서에 실제로 나온 문장(단어가 포함된 문장)을 그대로 짧게 인용한 뒤, 방금 배운 쉬운 뜻으로 그 문장을 1줄로 다시 풀어서 리마인드해 줘. (예: 교과서 문장 "대가야가 소멸되었다" → "대가야가 없어졌다는 뜻이에요!") 이 항목은 매번, 5개 단어 모두에 빠짐없이 출력해야 해.

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
- 📚 **교과서에서 다시 보기:** [교과서 원문 문장 짧게 인용 → 배운 쉬운 뜻으로 1줄 리마인드]
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
version = "v4.0 (단어장/속도 개선)"

st.title(f"📜 초등학생을 위한 쉬운 역사 사전 ({version} - {today})")
st.write("선생님에게 교과서 사진을 보여주고 궁금한 걸 물어보세요! 😊")

# API 키 설정 (Secrets 활용)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("앗! 시스템에 API 키가 설정되지 않았습니다. 관리자 페이지(Secrets)를 확인해 주세요.")
    api_key = None

# [세션 단어장] 오늘 배운 풀이를 임시 바구니에 누적 (보고서 Ⅳ-2 '1단계' 로드맵 반영)
if "vocab_log" not in st.session_state:
    st.session_state.vocab_log = []  # [{"time": "14:05", "content": "...", "keywords": [...]}]


# [속도 개선] 큰 사진(스마트폰 원본 3~10MB)을 서버로 그대로 보내면 업로드/판독이 느려짐.
# 긴 변 기준 1536px로 축소 + JPEG 변환하여 전송량을 줄인다. (체감 로딩 단축)
def compress_image(image_bytes, max_side=1536, quality=85):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        w, h = img.size
        scale = max(w, h) / max_side
        if scale > 1:
            img = img.resize((int(w / scale), int(h / scale)))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        return Image.open(buf)
    except Exception:
        # 압축 실패 시 원본으로 폴백
        return Image.open(io.BytesIO(image_bytes))


# 스트리밍 함수
def get_ai_response_stream(image_bytes, prompt_text, key):
    genai.configure(api_key=key)
    img_for_ai = compress_image(image_bytes)
    # temperature 0.2: 출력 양식 변동성(부록2 '출력값의 불안정성') 완화 목적으로 소폭 하향
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.2})
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
            # 안내 문구를 placeholder에 담아, 답변 완료 후 자동으로 지워지게 처리
            loading_placeholder = st.empty()
            loading_placeholder.info("선생님이 교과서를 꼼꼼히 읽고, 재미있는 이야기를 준비 중이에요! 🕵️‍♂️ (잠시만 기다려주세요...)")

            message_placeholder = st.empty()
            full_response = ""
            display_text = ""  # 스트림이 비어도 NameError가 나지 않도록 사전 초기화

            try:
                if user_question:
                    prompt_text = "학생의 추가 질문: '" + user_question + "'\n\n지시사항: 먼저 기본 5개 단어를 추출하고, 배경지식 이야기가 있으면 상황에 맞는 러시아 문화로 들려준 다음, 마지막 번호로 학생의 질문에 대답해. 각 단어의 '교과서에서 다시 보기' 항목은 절대 빠뜨리지 마."
                else:
                    prompt_text = "이 사진을 분석해서 다문화 아동이 어려워할 만한 단어를 정확히 5개 찾고, 한국 고유의 역사 이야기가 있다면 상황에 맞게 매칭된 배경지식 스토리텔링도 추가해 줘. 각 단어의 '교과서에서 다시 보기' 항목은 절대 빠뜨리지 마."

                # 제너레이터를 순회하며 텍스트 갱신
                for chunk in get_ai_response_stream(image_bytes_data, prompt_text, api_key):
                    # 안전장치: 세이프티 차단 등으로 text가 없는 청크는 건너뜀 (ValueError 방지)
                    try:
                        chunk_text = chunk.text
                    except Exception:
                        continue
                    if not chunk_text:
                        continue
                    full_response += chunk_text

                    # 화면 표시용 텍스트 (SEARCH_KEYWORD 태그는 숨김)
                    display_text = "\n".join(
                        line for line in full_response.split('\n')
                        if not line.startswith("SEARCH_KEYWORD:")
                    )
                    message_placeholder.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이\n" + display_text + "▌")

                # 출력이 끝나면 커서 제거 + 로딩 안내 제거
                loading_placeholder.empty()

                if not full_response.strip():
                    st.warning("앗, 선생님이 사진을 잘 못 읽었어요. 사진을 조금 더 밝고 크게 찍어서 다시 올려볼까요? 📷")
                else:
                    message_placeholder.markdown("### 👩‍🏫 친절한 역사 선생님의 맞춤 풀이\n" + display_text)
                    st.success("짜잔! 설명이 완성되었어요! 🎉")

                    # 구글 이미지 검색 링크 (중복 키워드 제거, 순서 유지)
                    keywords = []
                    for line in full_response.split('\n'):
                        if line.startswith("SEARCH_KEYWORD:"):
                            kw = line.replace("SEARCH_KEYWORD:", "").strip()
                            if kw and kw not in keywords:
                                keywords.append(kw)

                    if keywords:
                        st.markdown("---")
                        st.markdown("#### 🖼️ 사진으로 직접 확인해 볼까요?")
                        for keyword in keywords:
                            encoded_keyword = urllib.parse.quote(keyword)
                            google_url = f"https://www.google.com/search?tbm=isch&q={encoded_keyword}"
                            st.info(f"👉 **['{keyword}' 실제 사진 구글에서 찾아보기 (클릭!)]({google_url})**")

                    # [세션 단어장] 이번 풀이를 임시 바구니에 저장
                    st.session_state.vocab_log.append({
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "content": display_text,
                        "keywords": keywords,
                    })

            except Exception as e:
                loading_placeholder.empty()
                st.error("앗, 선생님이 잠깐 딴생각을 했나 봐요. 😅 잠시 후 다시 한번 [선생님께 여쭤보기!] 버튼을 눌러 주세요.")
                with st.expander("🔧 (선생님/봉사자용) 오류 상세 내용"):
                    st.code(str(e))

# ===================== 오늘 배운 단어장 (세션 누적) =====================
# 주의: Streamlit 세션 특성상 새로고침/창 닫기 시 사라짐 → 수업 종료 전 다운로드 안내
if st.session_state.vocab_log:
    st.markdown("---")
    with st.expander(f"📒 오늘 배운 단어장 보기 (풀이 {len(st.session_state.vocab_log)}개)"):
        st.caption("⚠️ 새로고침하거나 창을 닫으면 사라져요! 수업이 끝나기 전에 아래 버튼으로 꼭 저장해 주세요.")
        for i, entry in enumerate(st.session_state.vocab_log, 1):
            st.markdown(f"**[{i}] {entry['time']} 풀이** — 키워드: {', '.join(entry['keywords']) if entry['keywords'] else '없음'}")
        st.markdown("")

        # 다운로드용 마크다운(텍스트) 생성 — 오프라인 복습용 (보고서 Ⅳ-2 'PDF/파일 저장' 로드맵의 1단계 대응)
        export_lines = [f"# 📒 오늘 배운 역사 단어장 ({today})", ""]
        for i, entry in enumerate(st.session_state.vocab_log, 1):
            export_lines.append(f"## [{i}] {entry['time']} 풀이")
            export_lines.append(entry["content"])
            export_lines.append("")
        export_text = "\n".join(export_lines)

        st.download_button(
            label="💾 오늘 내 단어장 저장하기 (.txt)",
            data=export_text.encode("utf-8"),
            file_name=f"나의_역사_단어장_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )
        if st.button("🗑️ 단어장 비우기"):
            st.session_state.vocab_log = []
            st.rerun()