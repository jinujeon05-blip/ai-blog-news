import streamlit as st
from google import genai
import os
from bs4 import BeautifulSoup
import requests
import time

# 페이지 설정
st.set_page_config(
    page_title="10년 차 블로그 자동 생성기 v3",
    page_icon="✍️",
    layout="wide"
)

# 사이드바 설정 (API 키 입력)
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key 입력", type="password", help="Google Gemini API Key를 입력하세요.")
    st.markdown("---")
    st.markdown("### 💡 사용 Tip")
    st.markdown("- 뉴스 기사 URL이나 참고할 텍스트를 넣으세요.")
    st.markdown("- 10년 차 전문 블로거 스타일의 글과 **썸네일 가이드 & 해시태그**를 생성합니다.")

st.title("✍️ 10년 차 블로그 포스팅 자동화 마스터")
st.markdown("웹 주소나 뉴스 내용을 입력하면, 블로그 글 패키지(해시태그 포함)와 **마크다운 다운로드**, **썸네일 기획안**을 만들어 드립니다.")

# 입력 폼
tab1, tab2 = st.tabs(["🔗 웹 주소(URL)로 생성", "📝 직접 텍스트 입력"])

input_content = ""

with tab1:
    url_input = st.text_input("분석할 뉴스 또는 웹페이지 주소(URL)를 입력하세요.")
    if url_input:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url_input, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for script in soup(["script", "style", "nav", "footer"]):
                    script.decompose()
                input_content = soup.get_text(separator=' ', strip=True)[:3000]
                st.success("웹페이지 내용을 성공적으로 읽어왔습니다!")
            else:
                st.error(f"페이지를 불러오지 못했습니다. (상태 코드: {response.status_code})")
        except Exception as e:
            st.error(f"크롤링 중 오류가 발생했습니다: {e}")

with tab2:
    text_input = st.text_area("참고할 뉴스 내용이나 아이디어를 직접 적어주세요.", height=200)
    if text_input:
        input_content = text_input

# 블로그 카테고리/톤앤매너 선택
col1, col2 = st.columns(2)
with col1:
    blog_tone = st.selectbox(
        "블로그 글 분위기(톤앤매너)",
        ["친근하고 솔직한 후기/정보형 (10년 차 고수 스타일)", "전문적이고 분석적인 인사이트형", "트렌디하고 재치 있는 스타일"]
    )
with col2:
    target_platform = st.selectbox(
        "발행 플랫폼",
        ["네이버 블로그", "티스토리 / 워드프레스", "기타 플랫폼"]
    )

if st.button("🚀 블로그 포스팅 및 썸네일 가이드 생성하기", type="primary"):
    if not api_key:
        st.warning("먼저 사이드바에 Gemini API Key를 입력해주세요.")
    elif not input_content:
        st.warning("분석할 내용(URL 또는 텍스트)을 입력해주세요.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            with st.spinner("10년 차 블로거 스타일로 글, 썸네일 가이드, 해시태그를 작성하는 중입니다..."):
                prompt = f"""
                당신은 온라인에서 10년 동안 블로그를 운영하며 수많은 방문자를 모아온 '파워 블로거'이자 전문 콘텐츠 크리에이터입니다.
                아래에 제공된 내용(소스)을 바탕으로, 독자들이 끝까지 읽고 공감할 수 있는 고품질 블로그 포스팅 초안과 썸네일 가이드, 그리고 검색 노출용 해시태그를 작성해주세요.
                
                - 발행 플랫폼: {target_platform}
                - 톤앤매너: {blog_tone}

                [입력된 소스 내용]
                {input_content}

                [출력 양식]
                ### 📌 추천 블로그 제목
                (검색 유입이 잘 되고 클릭을 유도하는 매력적인 제목 3가지 추천)

                ### 👋 오프닝 (인사말)
                (독자의 공감을 사고 오늘 포스팅 주제로 자연스럽게 유도하는 첫인사)

                ### 📝 본문 내용
                (가독성이 좋도록 소제목, 이모지, 글머리 기호를 활용해 깊이 있게 정리된 본문)

                ### 🏁 클로징 (마무리 인사)
                (댓글 유도 및 다음 포스팅을 기대하게 만드는 자연스러운 마무리 인사말)

                ### 🏷️ 추천 해시태그
                (메인 키워드, 세부/연관 키워드, 트렌드 키워드를 포함해 복사하기 좋게 띄어쓰기로 구분된 해시태그 10~15개 추천, 예: #키워드1 #키워드2)

                ### 🎨 썸네일 이미지 디자인 가이드 및 문구
                - **배경 컨셉/이미지 추천**: (미드저니, 캔바 등에서 활용할 수 있는 시각적 묘사)
                - **썸네일 메인 문구 (텍스트)**: (클릭을 부르는 짧고 강렬한 핵심 문구 1~2줄)
                """

                # 사용 중이신 환경에 맞춘 3.5 Flash-Lite 모델 및 대체 모델 지정
                candidate_models = ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-3.6-flash']
                response = None
                last_error = None

                for model_name in candidate_models:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt
                        )
                        if response and response.text:
                            break
                    except Exception as err:
                        last_error = err
                        time.sleep(1)
                        continue

                if response is None or not response.text:
                    raise last_error

                blog_result = response.text

            # 결과 출력 영역
            st.markdown("---")
            st.subheader("🎉 완성된 블로그 포스팅 패키지")
            
            # 글 내용 표시
            st.markdown(blog_result)

            # 마크다운 파일(.md) 다운로드 버튼 추가
            st.markdown("---")
            st.download_button(
                label="📥 블로그 글 마크다운(.md) 파일로 다운로드",
                data=blog_result,
                file_name="blog_post.md",
                mime="text/markdown"
            )

            # 텍스트 원본 확인용 아코디언
            with st.expander("📋 전체 텍스트 원본 보기 및 복사"):
                st.text_area("텍스트 원본", blog_result, height=300)

        except Exception as e:
            st.error(f"블로그 포스팅 생성 중 오류가 발생했습니다: {e}")
