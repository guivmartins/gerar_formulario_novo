# app.py - Construtor de Formulários Completo 8.1 (com suporte drag & drop)
# Requisitos:
#   streamlit>=1.50.0
#   xmltodict
#   streamlit-sortables>=0.3.0

import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import xmltodict
from streamlit_sortables import sort_items

st.set_page_config(page_title="Construtor de Formulários Completo 8.1", layout="wide")

# --------------------------------------------
# Estado inicial
# --------------------------------------------
if "formulario" not in st.session_state:
    st.session_state.formulario = {
        "nome": "",
        "versao": "1.0",
        "secoes": [],
        "dominios": []
    }

if "nova_secao" not in st.session_state:
    st.session_state.nova_secao = {"titulo": "", "largura": 500, "elementos": []}

TIPOS_ELEMENTOS = [
    "texto", "texto-area", "data", "moeda", "cpf", "cnpj", "email",
    "telefone", "check", "comboBox", "comboFiltro", "grupoRadio",
    "grupoCheck", "paragrafo", "rotulo"
]

# --------------------------------------------
# Funções auxiliares
# --------------------------------------------
def _prettify_xml(root: ET.Element) -> str:
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    parsed = minidom.parseString(xml_bytes)
    return parsed.toprettyxml(indent="   ", encoding="utf-8").decode("utf-8")

def reorder_list_by_order(lista_original, nova_ordem):
    """Reordena a lista conforme a ordem retornada pelo componente de drag & drop."""
    nova_lista = [lista_original[int(i.split("_")[-1])] for i in nova_ordem]
    return nova_lista

# --------------------------------------------
# Função de geração XML
# --------------------------------------------
def gerar_xml(formulario: dict) -> str:
    root = ET.Element("gxsi:formulario", {
        "xmlns:gxsi": "http://www.w3.org/2001/XMLSchema-instance",
        "nome": formulario.get("nome", ""),
        "versao": formulario.get("versao", "1.0")
    })
    elementos = ET.SubElement(root, "elementos")
    dominios_global = ET.Element("dominios")

    for sec in formulario.get("secoes", []):
        sec_el = ET.SubElement(elementos, "elemento", {
            "gxsi:type": "seccao",
            "titulo": sec.get("titulo", ""),
            "largura": str(sec.get("largura", 500))
        })
        subelems = ET.SubElement(sec_el, "elementos")

        for item in sec.get("elementos", []):
            if item["tipo_elemento"] == "campo":
                campo = item["campo"]
                tipo = campo.get("tipo", "texto")
                titulo = campo.get("titulo", "")
                obrig = str(bool(campo.get("obrigatorio", False))).lower()
                largura = str(campo.get("largura", 450))
                if tipo in ["paragrafo", "rotulo"]:
                    ET.SubElement(subelems, "elemento", {
                        "gxsi:type": tipo,
                        "valor": campo.get("valor", campo.get("descricao", titulo)),
                        "largura": largura
                    })
                    continue
                if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] and campo.get("dominios"):
                    chave_dom = titulo.replace(" ", "")[:20].upper()
                    attrs = {
                        "gxsi:type": tipo,
                        "titulo": titulo,
                        "descricao": campo.get("descricao", titulo),
                        "obrigatorio": obrig,
                        "largura": largura,
                        "colunas": str(campo.get("colunas", 1)),
                        "dominio": chave_dom
                    }
                    ET.SubElement(subelems, "elemento", attrs)
                    dominio_el = ET.SubElement(dominios_global, "dominio", {
                        "gxsi:type": "dominioEstatico",
                        "chave": chave_dom
                    })
                    itens_el = ET.SubElement(dominio_el, "itens")
                    for d in campo["dominios"]:
                        ET.SubElement(itens_el, "item", {
                            "gxsi:type": "dominioItemValor",
                            "descricao": d["descricao"],
                            "valor": d["valor"]
                        })
                    continue
                attrs = {
                    "gxsi:type": tipo,
                    "titulo": titulo,
                    "descricao": campo.get("descricao", titulo),
                    "obrigatorio": obrig,
                    "largura": largura
                }
                if tipo == "texto-area" and campo.get("altura"):
                    attrs["altura"] = str(campo.get("altura"))
                ET.SubElement(subelems, "elemento", attrs)
    root.append(dominios_global)
    return _prettify_xml(root)

# --------------------------------------------
# Função de pré-visualização (mantida)
# --------------------------------------------
def preview_formulario(formulario: dict):
    st.header("📋 Pré-visualização do Formulário")
    st.subheader(formulario.get("nome", ""))
    for sec in formulario.get("secoes", []):
        st.markdown(f"### {sec.get('titulo')}")
        for item in sec.get("elementos", []):
            if item["tipo_elemento"] == "campo":
                campo = item["campo"]
                tipo = campo.get("tipo")
                if tipo == "texto":
                    st.text_input(campo.get("titulo", ""))
                elif tipo == "texto-area":
                    st.text_area(campo.get("titulo", ""), height=campo.get("altura", 100))
                elif tipo == "data":
                    st.date_input(campo.get("titulo", ""))
                elif tipo == "check":
                    st.checkbox(campo.get("titulo", ""))
                elif tipo == "grupoRadio":
                    st.radio(campo.get("titulo", ""), [d["descricao"] for d in campo.get("dominios", [])])
                elif tipo == "grupoCheck":
                    st.markdown(f"**{campo.get('titulo', '')}**")
                    for d in campo.get("dominios", []):
                        st.checkbox(d["descricao"])
                elif tipo in ["comboBox", "comboFiltro"]:
                    st.multiselect(campo.get("titulo", ""), [d["descricao"] for d in campo.get("dominios", [])])
                elif tipo == "rotulo":
                    st.markdown(f"**{campo.get('valor') or campo.get('titulo')}**")
                elif tipo == "paragrafo":
                    st.markdown(campo.get("valor") or campo.get("titulo", ""))

# --------------------------------------------
# Interface principal
# --------------------------------------------
tab1, tab2 = st.tabs(["Construtor", "Importar"])

with tab1:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.title("Construtor de Formulários Completo 8.1 🧱")
        st.session_state.formulario["nome"] = st.text_input("Nome do Formulário", st.session_state.formulario["nome"])
        st.markdown("---")

        # Adicionar seção
        with st.expander("➕ Adicionar Seção", expanded=True):
            st.session_state.nova_secao["titulo"] = st.text_input("Título da Seção", st.session_state.nova_secao["titulo"])
            st.session_state.nova_secao["largura"] = st.number_input("Largura", min_value=100, value=st.session_state.nova_secao["largura"], step=10)
            if st.button("Salvar Seção"):
                if st.session_state.nova_secao["titulo"]:
                    st.session_state.formulario["secoes"].append(st.session_state.nova_secao.copy())
                    st.session_state.nova_secao = {"titulo": "", "largura": 500, "elementos": []}
                    st.rerun()

        # Ordenar seções por drag & drop
        if st.session_state.formulario["secoes"]:
            st.subheader("📂 Seções (arraste para reordenar)")
            secao_labels = [f"{i+1}. {sec['titulo']}" for i, sec in enumerate(st.session_state.formulario["secoes"])]
            new_order = sort_items(secao_labels, direction="vertical", key="order_sections")
            if new_order != secao_labels:
                st.session_state.formulario["secoes"] = reorder_list_by_order(st.session_state.formulario["secoes"], new_order)
                st.rerun()

        # Mostrar seções e permitir ordenar elementos
        for s_idx, sec in enumerate(st.session_state.formulario.get("secoes", [])):
            with st.expander(f"📁 {sec.get('titulo','(sem título)')}", expanded=False):
                st.write(f"Largura: {sec.get('largura', 500)} px")

                if sec.get("elementos"):
                    st.markdown("**🧩 Elementos (arraste para reordenar)**")
                    elementos_labels = []
                    for i, el in enumerate(sec["elementos"]):
                        if el["tipo_elemento"] == "campo":
                            label = f"Campo: {el['campo'].get('titulo','')}"
                        else:
                            label = f"Tabela: {i+1}"
                        elementos_labels.append(f"el_{i} | {label}")

                    new_order = sort_items(elementos_labels, direction="vertical", key=f"order_{s_idx}")
                    if new_order != elementos_labels:
                        sec["elementos"] = reorder_list_by_order(sec["elementos"], new_order)
                        st.rerun()

                if st.button(f"🗑️ Excluir Seção", key=f"del_sec_{s_idx}"):
                    st.session_state.formulario["secoes"].pop(s_idx)
                    st.rerun()

            st.markdown("---")

    # Coluna direita: pré-visualização
    with col2:
        preview_formulario(st.session_state.formulario)
        st.markdown("---")
        st.subheader("📑 Pré-visualização XML")
        xml_code = gerar_xml(st.session_state.formulario)
        st.code(xml_code, language="xml")

with tab2:
    st.title("Importar Arquivo de Formulário")
    uploaded_file = st.file_uploader("Escolha o arquivo XML", type=["xml", "gfe"])
    if uploaded_file:
        try:
            content = uploaded_file.read()
            dict_parsed = xmltodict.parse(content)
            if "gxsi:formulario" in dict_parsed:
                st.success("Importação OK (estrutura básica).")
            else:
                st.error("Arquivo não contém estrutura gxsi:formulario.")
        except Exception as e:
            st.error(f"Erro: {str(e)}")
