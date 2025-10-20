import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom

st.set_page_config(page_title="Construtor de Formulários 7.6", layout="wide")

if "formulario" not in st.session_state:
    st.session_state.formulario = {
        "nome": "",
        "versao": "1.0",
        "secoes": [],
        "dominios": []
    }
if "nova_secao" not in st.session_state:
    st.session_state.nova_secao = {"titulo": "", "largura": 500, "campos": []}

TIPOS_ELEMENTOS = [
    "texto", "texto-area", "data", "moeda", "cpf", "cnpj", "email",
    "telefone", "check", "comboBox", "comboFiltro", "grupoRadio",
    "grupoCheck", "paragrafo", "rotulo"
]

def _prettify_xml(root: ET.Element) -> str:
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    parsed = minidom.parseString(xml_bytes)
    return parsed.toprettyxml(indent="   ", encoding="utf-8").decode("utf-8")

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
        tabelas = sec.get("tabelas", [])

        if tabelas:
            for tabela in tabelas:
                tabela_el = ET.SubElement(subelems, "elemento", {"gxsi:type": "tabela"})
                linhas_tag = ET.SubElement(tabela_el, "linhas")
                for linha in tabela:
                    linha_tag = ET.SubElement(linhas_tag, "linha")
                    celulas_tag = ET.SubElement(linha_tag, "celulas")
                    for celula in linha:
                        celula_tag = ET.SubElement(celulas_tag, "celula", {"linhas": "1", "colunas": "1"})
                        elementos_tag = ET.SubElement(celula_tag, "elementos")
                        for campo in celula:
                            tipo = campo.get("tipo", "texto")
                            titulo = campo.get("titulo", "")
                            obrig = str(bool(campo.get("obrigatorio", False))).lower()
                            largura = str(campo.get("largura", 450))
                            if tipo in ["paragrafo", "rotulo"]:
                                ET.SubElement(elementos_tag, "elemento", {
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
                                ET.SubElement(elementos_tag, "elemento", attrs)
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
                            el = ET.SubElement(elementos_tag, "elemento", attrs)
                            ET.SubElement(el, "conteudo", {"gxsi:type": "valor"})

        for campo in sec.get("campos", []):
            if campo.get("in_tabela", False):
                continue
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
            el = ET.SubElement(subelems, "elemento", attrs)
            ET.SubElement(el, "conteudo", {"gxsi:type": "valor"})

    root.append(dominios_global)
    return _prettify_xml(root)

def preview_formulario(formulario: dict, context_key: str = "main"):
    st.header("📋 Pré-visualização do Formulário")
    st.subheader(formulario.get("nome", ""))
    for s_idx, sec in enumerate(formulario.get("secoes", [])):
        st.markdown(f"### {sec.get('titulo')}")
        tabelas = sec.get("tabelas", [])
        for tabela_idx, tabela in enumerate(tabelas):
            st.markdown(f"**Tabela {tabela_idx+1}**")
            for linha_idx, linha in enumerate(tabela):
                cols = st.columns(len(linha)) if linha else []
                for c_idx, celula in enumerate(linha):
                    if cols:
                        with cols[c_idx]:
                            for c_idx2, campo in enumerate(celula):
                                tipo = campo.get("tipo")
                                key_prev = f"prev_{context_key}_{s_idx}_t{tabela_idx}_l{linha_idx}_c{c_idx}_f{c_idx2}_{sec.get('titulo')}_{campo.get('titulo')}"
                                if tipo == "texto":
                                    st.text_input(campo.get("titulo", ""), key=key_prev)
                                elif tipo == "texto-area":
                                    st.text_area(campo.get("titulo", ""), height=campo.get("altura", 100), key=key_prev)
                                elif tipo == "data":
                                    st.date_input(campo.get("titulo", ""), key=key_prev)
                                elif tipo == "grupoCheck":
                                    st.markdown(f"**{campo.get('titulo', '')}**")
                                    for idx, dom in enumerate(campo.get("dominios", [])):
                                        st.checkbox(dom["descricao"], key=f"{key_prev}_{idx}")
                                elif tipo in ["comboBox", "comboFiltro"]:
                                    st.multiselect(campo.get("titulo", ""), [d["descricao"] for d in campo.get("dominios", [])], key=key_prev)
                                elif tipo == "grupoRadio":
                                    st.radio(campo.get("titulo", ""), [d["descricao"] for d in campo.get("dominios", [])], key=key_prev)
                                elif tipo == "check":
                                    st.checkbox(campo.get("titulo", ""), key=key_prev)
                                elif tipo == "rotulo":
                                    conteudo = campo.get("valor") or campo.get("descricao") or campo.get("titulo") or ""
                                    st.markdown(f"**{conteudo}**")
                                elif tipo == "paragrafo":
                                    conteudo = campo.get("valor") or campo.get("descricao") or campo.get("titulo") or ""
                                    conteudo = str(conteudo).replace("\\n", "\n")
                                    st.markdown(conteudo)
        for c_idx, campo in enumerate(sec.get("campos", [])):
            if campo.get("in_tabela"):
                continue
            tipo = campo.get("tipo")
            key_prev = f"prev_{context_key}_{s_idx}_{c_idx}_{sec.get('titulo')}_{campo.get('titulo')}"
            if tipo == "texto":
                st.text_input(campo.get("titulo", ""), key=key_prev)
            elif tipo == "texto-area":
                st.text_area(campo.get("titulo", ""), height=campo.get("altura", 100), key=key_prev)
            elif tipo == "data":
                st.date_input(campo.get("titulo", ""), key=key_prev)
            elif tipo == "grupoCheck":
                st.markdown(f"**{campo.get('titulo', '')}**")
                for idx, dom in enumerate(campo.get("dominios", [])):
                    st.checkbox(dom["descricao"], key=f"{key_prev}_{idx}")
            elif tipo in ["comboBox", "comboFiltro"]:
                st.multiselect(campo.get("titulo", ""), [d["descricao"] for d in campo.get("dominios", [])], key=key_prev)
            elif tipo == "grupoRadio":
                st.radio(campo.get("titulo", ""), [d["descricao"] for d in campo.get("dominios", [])], key=key_prev)
            elif tipo == "check":
                st.checkbox(campo.get("titulo", ""), key=key_prev)
            elif tipo == "rotulo":
                st.markdown(f"**{campo.get('valor') or campo.get('descricao') or campo.get('titulo') or ''}**")
            elif tipo == "paragrafo":
                conteudo = campo.get("valor") or campo.get("descricao") or campo.get("titulo") or ""
                conteudo = str(conteudo).replace("\\n", "\n")
                st.markdown(conteudo)

def adicionar_campo_secao(secao, campo, linha_num=None, finalizar_tabela=False):
    if campo.get("in_tabela"):
        if not secao.get("tabela_aberta", False):
            secao["tabelas"] = secao.get("tabelas", [])
            secao["tabela_aberta"] = True
            secao["tabela_atual"] = []
            secao["linha_atual_num"] = None
        if linha_num is None:
            st.warning("Informe número da linha para inserir na tabela.")
            return
        if secao["linha_atual_num"] != linha_num:
            secao["linha_atual_num"] = linha_num
            secao["tabela_atual"].append([])
        linha_atual = secao["tabela_atual"][-1]
        # cada célula recebe 1 campo, adiciona nova célula para cada campo na linha
        linha_atual.append([campo])
        if finalizar_tabela:
            secao["tabelas"].append(secao["tabela_atual"])
            secao["tabela_atual"] = []
            secao["tabela_aberta"] = False
            secao["linha_atual_num"] = None
            st.success("Tabela finalizada.")
    else:
        if secao.get("tabela_aberta", False):
            if secao.get("linha_atual_num") is not None:
                secao["linha_atual_num"] = None
            secao["tabelas"].append(secao["tabela_atual"])
            secao["tabela_atual"] = []
            secao["tabela_aberta"] = False
        secao.setdefault("campos", []).append(campo)

aba = st.tabs(["Construtor", "Importar arquivo"])

with aba[0]:
    col1, col2 = st.columns(2)
    with col1:
        st.title("Construtor de Formulários 7.6")
        st.session_state.formulario["nome"] = st.text_input("Nome do Formulário", st.session_state.formulario["nome"])
        st.markdown("---")
        with st.expander("➕ Adicionar Seção", expanded=True):
            st.session_state.nova_secao["titulo"] = st.text_input("Título da Seção", st.session_state.nova_secao["titulo"])
            st.session_state.nova_secao["largura"] = st.number_input("Largura da Seção", min_value
