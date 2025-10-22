import streamlit as st

st.set_page_config(page_title="Debug State Session", layout="wide")

# Exibir todo o estado da sessão para depuração
st.write("Estado atual do st.session_state:")
st.write(dict(st.session_state))

aba = st.tabs(["Construtor", "Importar arquivo"])

if "formulario" not in st.session_state:
    st.session_state.formulario = {
        "nome": "formulário inicial",
        "versao": "1.0",
        "secoes": [
            {"titulo": "Seção teste 1", "largura": 500, "elementos": []},
            {"titulo": "Seção teste 2", "largura": 500, "elementos": []}
        ],
        "dominios": []
    }

with aba[0]:
    st.title("Construtor")
    nome_form = st.text_input("Nome do Formulário", st.session_state.formulario.get("nome", ""))
    st.session_state.formulario["nome"] = nome_form

    secoes = st.session_state.formulario.get("secoes", [])
    st.write(f"Seções disponíveis: {len(secoes)}")
    for idx, secao in enumerate(secoes):
        st.write(f"{idx + 1}: {secao.get('titulo', '(sem título)')}")

with aba[1]:
    st.title("Importar Arquivo de Formulário")
    uploaded_file = st.file_uploader("Escolha o arquivo XML", type=["xml", "gfe"])
    if uploaded_file:
        st.write("Arquivo carregado, mas importação não implementada nesta versão.")
