import streamlit as st

st.set_page_config(page_title="Construtor Incremental 1", layout="wide")

aba = st.tabs(["Construtor", "Importar arquivo"])

if "formulario" not in st.session_state:
    st.session_state.formulario = {
        "nome": "",
        "versao": "1.0",
        "secoes": [],
        "dominios": []
    }

with aba[0]:
    st.title("Construtor de Formulários Incremental")
    nome_form = st.text_input("Nome do Formulário", st.session_state.formulario.get("nome", ""))
    st.session_state.formulario["nome"] = nome_form

    secoes = st.session_state.formulario.get("secoes", [])
    st.write(f"Quantidade de seções: {len(secoes)}")
    for i, secao in enumerate(secoes):
        st.write(f"Seção {i+1}: {secao.get('titulo', '')}")

with aba[1]:
    st.title("Importar Arquivo de Formulário")
    uploaded_file = st.file_uploader("Escolha o arquivo XML para importar", type=["xml", "gfe"])
    if uploaded_file is not None:
        st.write("Arquivo carregado. (Implementar importação)")

st.write("Fim do app incremental")
