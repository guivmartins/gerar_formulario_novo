import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import xmltodict

st.set_page_config(page_title="Construtor de Formulários 8.0", layout="wide")

aba = st.tabs(["Construtor", "Importar arquivo"])

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
                        "valor": titulo,
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
                    for d in campo.get("dominios", []):
                        ET.SubElement(itens_el, "item", {
                            "gxsi:type": "dominioItemValor",
                            "descricao": d.get("descricao", ""),
                            "valor": d.get("valor", "")
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

            elif item["tipo_elemento"] == "tabela":
                tabela = item["tabela"]
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
                                    "valor": titulo,
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
                                for d in campo.get("dominios", []):
                                    ET.SubElement(itens_el, "item", {
                                        "gxsi:type": "dominioItemValor",
                                        "descricao": d.get("descricao", ""),
                                        "valor": d.get("valor", "")
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
                            ET.SubElement(elementos_tag, "elemento", attrs)

    root.append(dominios_global)
    return _prettify_xml(root)

def preview_formulario(formulario: dict, context_key: str = "main"):
    st.header("📋 Pré-visualização do Formulário")
    st.subheader(formulario.get("nome", ""))
    for s_idx, sec in enumerate(formulario.get("secoes", [])):
        st.markdown(f"### {sec.get('titulo')}")
        elementos_lista = sec.get("elementos", [])
        for idx, item in enumerate(elementos_lista):
            if item["tipo_elemento"] == "campo":
                campo = item["campo"]
                tipo = campo.get("tipo")
                key_prev = f"prev_{context_key}_{s_idx}_{idx}_{sec.get('titulo')}_{campo.get('titulo')}"
                if tipo == "texto":
                    st.text_input(campo.get("titulo", ""), key=key_prev)
                elif tipo == "texto-area":
                    st.text_area(campo.get("titulo", ""), height=campo.get("altura", 100), key=key_prev)
                elif tipo == "data":
                    st.date_input(campo.get("titulo", ""), key=key_prev)
                elif tipo == "grupoCheck":
                    st.markdown(f"**{campo.get('titulo', '')}**")
                    for i, dom in enumerate(campo.get("dominios", [])):
                        st.checkbox(dom["descricao"], key=f"{key_prev}_{i}")
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

            elif item["tipo_elemento"] == "tabela":
                tabela = item["tabela"]
                st.markdown("**Tabela**")
                for linha_idx, linha in enumerate(tabela):
                    cols = st.columns(len(linha))
                    for c_idx, celula in enumerate(linha):
                        with cols[c_idx]:
                            for c_idx2, campo in enumerate(celula):
                                tipo = campo.get("tipo")
                                key_prev = f"prev_{context_key}_{s_idx}_t{idx}_l{linha_idx}_c{c_idx}_f{c_idx2}_{sec.get('titulo')}_{campo.get('titulo')}"
                                if tipo == "texto":
                                    st.text_input(campo.get("titulo", ""), key=key_prev)
                                elif tipo == "texto-area":
                                    st.text_area(campo.get("titulo", ""), height=campo.get("altura", 100), key=key_prev)
                                elif tipo == "data":
                                    st.date_input(campo.get("titulo", ""), key=key_prev)
                                elif tipo == "grupoCheck":
                                    st.markdown(f"**{campo.get('titulo', '')}**")
                                    for i, dom in enumerate(campo.get("dominios", [])):
                                        st.checkbox(dom["descricao"], key=f"{key_prev}_{i}")
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

def adicionar_campo_secao(secao, campo, linha_num=None):
    if campo.get("in_tabela"):
        if not secao.get("tabela_aberta", False):
            secao["tabela_aberta"] = True
            secao["tabela_atual"] = []
            secao["linha_atual_num"] = None
            if "elementos" not in secao:
                secao["elementos"] = []
        if linha_num is None:
            st.warning("Informe número da linha para inserir na tabela.")
            return
        if secao["linha_atual_num"] != linha_num:
            secao["linha_atual_num"] = linha_num
            secao["tabela_atual"].append([])
        linha_atual = secao["tabela_atual"][-1]
        linha_atual.append([campo])
        if not any(el.get("tipo_elemento") == "tabela" and el.get("tabela") == secao["tabela_atual"] for el in secao.get("elementos", [])):
            secao["elementos"].append({"tipo_elemento": "tabela", "tabela": secao["tabela_atual"]})
    else:
        if secao.get("tabela_aberta", False):
            if secao.get("linha_atual_num") is not None:
                secao["linha_atual_num"] = None
            if not any(el.get("tipo_elemento") == "tabela" and el.get("tabela") == secao["tabela_atual"] for el in secao.get("elementos", [])):
                secao["elementos"].append({"tipo_elemento": "tabela", "tabela": secao["tabela_atual"]})
            secao["tabela_atual"] = []
            secao["tabela_aberta"] = False
        if "elementos" not in secao:
            secao["elementos"] = []
        secao["elementos"].append({"tipo_elemento": "campo", "campo": campo})

def reorder_elementos(elementos, idx, direcao):
    novo_idx = idx + direcao
    if novo_idx < 0 or novo_idx >= len(elementos):
        return elementos
    elementos[idx], elementos[novo_idx] = elementos[novo_idx], elementos[idx]
    return elementos

with aba[1]:
    st.title("Importar Arquivo de Formulário")
    uploaded_file = st.file_uploader("Escolha o arquivo XML para importar", type=["xml", "gfe"])
    if uploaded_file is not None:
        try:
            content = uploaded_file.read()
            dict_parsed = xmltodict.parse(content)
            formulario_dict = {}
            form_data = dict_parsed.get("gxsi:formulario", {})
            if not form_data or not form_data.get("elementos"):
                st.error("Arquivo não contém estrutura válida de formulário ou está incompleto.")
            else:
                formulario_dict["nome"] = form_data.get("@nome", "")
                formulario_dict["versao"] = form_data.get("@versao", "1.0")
                formulario_dict["secoes"] = []
                elementos = form_data["elementos"].get("elemento", [])
                if not isinstance(elementos, list):
                    elementos = [elementos] if elementos else []
                for elem in elementos:
                    if elem and elem.get("@gxsi:type") == "seccao":
                        sec = {
                            "titulo": elem.get("@titulo", ""),
                            "largura": int(elem.get("@largura", "500")),
                            "elementos": []
                        }
                        sec_elementos = elem.get("elementos", {}).get("elemento", [])
                        if not isinstance(sec_elementos, list):
                            sec_elementos = [sec_elementos] if sec_elementos else []
                        for se in sec_elementos:
                            tipo = se.get("@gxsi:type") if se else ""
                            if tipo == "tabela":
                                linhas = se.get("linhas", {}).get("linha", []) if se.get("linhas") else []
                                if not isinstance(linhas, list):
                                    linhas = [linhas] if linhas else []
                                tabela = []
                                for linha in linhas:
                                    celulas = linha.get("celulas", {}).get("celula", []) if linha.get("celulas") else []
                                    if not isinstance(celulas, list):
                                        celulas = [celulas] if celulas else []
                                    linha_lista = []
                                    for cel in celulas:
                                        elementos_cel = cel.get("elementos", {}).get("elemento", []) if cel.get("elementos") else []
                                        if not isinstance(elementos_cel, list):
                                            elementos_cel = [elementos_cel] if elementos_cel else []
                                        campos = []
                                        for c in elementos_cel:
                                            c_info = {
                                                "tipo": c.get("@gxsi:type", "texto") if c else "",
                                                "titulo": c.get("@titulo", "") if c else "",
                                                "descricao": c.get("@descricao", "") if c else "",
                                                "obrigatorio": (c.get("@obrigatorio", "false") == "true") if c else False,
                                                "largura": int(c.get("@largura", "450")) if c and c.get("@largura") else 450,
                                                "altura": int(c.get("@altura", "0")) if c and c.get("@altura") else None,
                                                "colunas": int(c.get("@colunas", "1")) if c and c.get("@colunas") else 1
                                            }
                                            campos.append(c_info)
                                        linha_lista.append(campos)
                                    tabela.append(linha_lista)
                                sec["elementos"].append({"tipo_elemento": "tabela", "tabela": tabela})
                            else:
                                c_info = {
                                    "tipo": tipo,
                                    "titulo": se.get("@titulo", "") if se else "",
                                    "descricao": se.get("@descricao", "") if se else "",
                                    "obrigatorio": (se.get("@obrigatorio", "false") == "true") if se else False,
                                    "largura": int(se.get("@largura", "450")) if se and se.get("@largura") else 450,
                                    "altura": int(se.get("@altura", "0")) if se and se.get("@altura") else None,
                                    "colunas": int(se.get("@colunas", "1")) if se and se.get("@colunas") else 1,
                                    "in_tabela": False,
                                    "dominios": []
                                }
                                sec["elementos"].append({"tipo_elemento": "campo", "campo": c_info})
                        formulario_dict["secoes"].append(sec)
                st.session_state.formulario = formulario_dict
                st.success("Arquivo importado com sucesso!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar arquivo: {str(e)}")
