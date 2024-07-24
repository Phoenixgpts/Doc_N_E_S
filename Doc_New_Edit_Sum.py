import streamlit as st
from openai import OpenAI
from docx import Document
from io import BytesIO
import os
import requests
from dotenv import load_dotenv
import tiktoken
from typing import List

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 키를 환경 변수에서 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")

# API 키 검증
if not openai_api_key:
    st.error("OpenAI API 키가 설정되지 않았습니다. 환경 변수를 확인해주세요.")
    st.stop()

st.set_page_config(
    page_title="Document NEW + EDIT + SUM",
    page_icon="📄",
)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=openai_api_key)

generation_config = {
    "temperature": 0.4,
    "top_p": 0.95,
}

# 사이드바에서 모델 선택
model_selection = st.sidebar.radio("**사용할 모델을 선택하세요 :**", ("Phoenix-GPT4o", "Phoenix-GPT4o-Mini"), captions=("가격↑/성능↑/속도↓", "가격↓/성능↓/속도↑"))
model_name = "gpt-4" if model_selection == "Phoenix-GPT4o" else "gpt-4o-mini"

st.title("Document NEW + EDIT + SUM")
st.caption("By Phoenix AI")

def split_text(text: str, max_tokens: int = 8000) -> List[str]:
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunks = []
    
    for i in range(0, len(tokens), max_tokens):
        chunk = encoding.decode(tokens[i:i + max_tokens])
        chunks.append(chunk)
    
    return chunks

language_prompts = {
    "한국어": "이 키워드에 대한 2,000자 길이의 문서를 한국어로 생성해줘.",
    "영어": "Generate a 2,000-character document for this keyword in English.",
    "일본어": "このキーワードについて2,000文字の日本語のドキュメントを作成してください。",
    "중국어": "请用中文生成关于这个关键词的2,000字文档。",
    "러시아어": "Создайте документ на 2,000 символов по этому ключевому слову на русском языке.",
    "프랑스어": "Générez un document de 2,000 caractères pour ce mot-clé en français.",
    "독일어": "Erstellen Sie ein 2,000 Zeichen langes Dokument für dieses Schlüsselwort auf Deutsch.",
    "이탈리아어": "Genera un documento di 2,000 caratteri per questa parola chiave in italiano."
}

# 1. Doc-New
st.header("1. Doc-New")
keyword = st.text_input("생성할 문서의 키워드를 입력해 주세요:")
output_language_new = st.selectbox("생성한 문서의 출력 언어를 선택하세요", list(language_prompts.keys()), key="new_language")
if st.button("문서 생성") and keyword:
    with st.spinner("문서를 생성하는 중입니다..."):
        system_instruction = language_prompts[output_language_new]
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": keyword}
                ],
                max_tokens=2000,
                **generation_config
            )
            result_text = response.choices[0].message.content.strip()
            st.session_state.result_text = result_text
            st.success(result_text)
        except Exception as e:
            st.error(f"문서 생성 중 오류가 발생했습니다: {str(e)}")

# 2. Doc-Edit
st.header("2. Doc-Edit")
uploaded_file_edit = st.file_uploader("수정할 문서를 업로드 해 주세요", type=["docx"], key="edit_file")
uploaded_link_edit = st.text_input("수정할 문서의 링크를 입력해 주세요:", key="edit_link")

doc_text_edit = ""
if uploaded_file_edit:
    doc_text_edit = "\n".join([para.text for para in Document(uploaded_file_edit).paragraphs])
elif uploaded_link_edit:
    response = requests.get(uploaded_link_edit)
    if response.status_code == 200:
        doc_text_edit = response.text
    else:
        st.error("문서 링크를 불러오는 데 실패했습니다.")

if doc_text_edit:
    st.text_area("문서 내용", doc_text_edit, height=300)
    edit_keyword = st.text_input("수정할 키워드 또는 문장을 입력해 주세요:")
    output_language_edit = st.selectbox("수정한 문서의 출력 언어를 선택하세요:", list(language_prompts.keys()), key="edit_language")
    if st.button("문서 수정") and edit_keyword:
        with st.spinner("문서를 수정하는 중입니다..."):
            system_instruction = language_prompts[output_language_edit]
            chunks = split_text(doc_text_edit)
            edited_chunks = []
            for i, chunk in enumerate(chunks):
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": f"{edit_keyword}\n\n{chunk}"}
                        ],
                        max_tokens=2000,
                        **generation_config
                    )
                    edited_chunks.append(response.choices[0].message.content.strip())
                    st.progress((i + 1) / len(chunks))
                except Exception as e:
                    st.error(f"문서 수정 중 오류가 발생했습니다 (파트 {i+1}): {str(e)}")
                    break
            edited_text = "\n\n".join(edited_chunks)
            st.session_state.edited_text = edited_text
            st.success(edited_text)

# 3. Doc-SUM
st.header("3. Doc-SUM")
uploaded_file_sum = st.file_uploader("요약할 문서를 업로드 해 주세요", type=["docx"], key="sum_file")
uploaded_link_sum = st.text_input("요약할 문서의 링크를 입력해 주세요:", key="sum_link")

doc_text_sum = ""
if uploaded_file_sum:
    doc_text_sum = "\n".join([para.text for para in Document(uploaded_file_sum).paragraphs])
elif uploaded_link_sum:
    response = requests.get(uploaded_link_sum)
    if response.status_code == 200:
        doc_text_sum = response.text
    else:
        st.error("문서 링크를 불러오는 데 실패했습니다.")

if doc_text_sum:
    st.text_area("요약할 문서 내용", doc_text_sum, height=300)
    sum_keyword = st.text_input("요약할 키워드 또는 문장을 입력해 주세요:")
    output_language_sum = st.selectbox("요약한 문서의 출력 언어를 선택하세요:", list(language_prompts.keys()), key="sum_language")
    if st.button("문서 요약") and sum_keyword:
        with st.spinner("문서를 요약하는 중입니다..."):
            system_instruction = language_prompts[output_language_sum]
            chunks = split_text(doc_text_sum)
            summarized_chunks = []
            for i, chunk in enumerate(chunks):
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": f"{sum_keyword}\n\n{chunk}"}
                        ],
                        max_tokens=1000,
                        **generation_config
                    )
                    summarized_chunks.append(response.choices[0].message.content.strip())
                    st.progress((i + 1) / len(chunks))
                except Exception as e:
                    st.error(f"문서 요약 중 오류가 발생했습니다 (파트 {i+1}): {str(e)}")
                    break
            
            if len(summarized_chunks) > 1:
                final_summary = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "Combine the following summaries into one coherent summary:"},
                        {"role": "user", "content": "\n\n".join(summarized_chunks)}
                    ],
                    max_tokens=2000,
                    **generation_config
                )
                summarized_text = final_summary.choices[0].message.content.strip()
            else:
                summarized_text = summarized_chunks[0] if summarized_chunks else ""

            st.session_state.summarized_text = summarized_text
            st.success(summarized_text)
