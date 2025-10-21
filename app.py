import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import xmltodict

st.set_page_config(page_title="Construtor de Formulários Completo 7.14", layout="wide")

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

# Interface
aba = st.tabs(["Construtor", "Importar arquivo"])

with aba[0]:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.title("Construtor de Formulários Completo 7.14")
        st.session_state.formulario["nome"] = st.text_input("Nome do Formulário", st.session_state.formulario["nome"])
        st.markdown("---")

        with st.expander("➕ Adicionar Seção", expanded=True):
            st.session_state.nova_secao["titulo"] = st.text_input("Título da Seção", st.session_state.nova_secao["titulo"])
            st.session_state.nova_secao["largura"] = st.number_input("Largura da Seção", min_value=100, value=st.session_state.nova_secao["largura"], step=10)
            if st.button("Salvar Seção"):
                if st.session_state.nova_secao["titulo"]:
                    st.session_state.formulario["secoes"].append(st.session_state.nova_secao.copy())
                    st.session_state.nova_secao = {"titulo": "", "largura": 500, "elementos": []}
                    st.rerun()

        st.markdown("---")

        for s_idx, sec in enumerate(st.session_state.formulario.get("secoes", [])):
            with st.expander(f"📁 Seção: {sec.get('titulo','(sem título)')}", expanded=False):
                st.write(f"**Largura:** {sec.get('largura', 500)}")
                if st.button(f"🗑️ Excluir Seção", key=f"del_sec_{s_idx}"):
                    st.session_state.formulario["secoes"].pop(s_idx)
                    st.rerun()

                st.markdown("### Elementos na Seção (ordem mantida)")
                elementos = sec.get("elementos", [])
                for i, item in enumerate(elementos):
                    col_ord1, col_ord2, col_main, col_exc = st.columns([1, 1, 10, 1])
                    with col_ord1:
                        if st.button("⬆️", key=f"up_{s_idx}_{i}"):
                            sec["elementos"] = reorder_elementos(elementos, i, -1)
                            st.rerun()
                    with col_ord2:
                        if st.button("⬇️", key=f"down_{s_idx}_{i}"):
                            sec["elementos"] = reorder_elementos(elementos, i, 1)
                            st.rerun()
                    with col_main:
                        if item["tipo_elemento"] == "campo":
                            st.text(f"Campo: {item['campo'].get('titulo', '')}")
                        elif item["tipo_elemento"] == "tabela":
                            st.markdown(f"**Tabela:**")
                            for l_idx, linha in enumerate(item["tabela"]):
                                cel_textos = []
                                for c_idx, celula in enumerate(linha):
                                    titulos = ", ".join([c.get("titulo", "") for c in celula])
                                    cel_textos.append(f"Celula {c_idx+1}: {titulos}")
                                st.text(f"Linha {l_idx+1}: " + " | ".join(cel_textos))
                    with col_exc:
                        if st.button("❌", key=f"del_{s_idx}_{i}"):
                            elementos.pop(i)
                            st.rerun()

        if st.session_state.formulario.get("secoes"):
            secao_opcoes = [sec.get("titulo", f"Seção {i}") for i, sec in enumerate(st.session_state.formulario["secoes"])]
            indice_selecao = st.selectbox("Selecione a Seção para adicionar um campo", options=range(len(secao_opcoes)), format_func=lambda i: secao_opcoes[i])
            secao_atual = st.session_state.formulario["secoes"][indice_selecao]

            with st.expander(f"➕ Adicionar Campos à seção: {secao_atual.get('titulo','')}", expanded=True):
                tipo = st.selectbox("Tipo do Campo", TIPOS_ELEMENTOS, key=f"type_add_{indice_selecao}")
                titulo = st.text_input("Título do Campo", key=f"title_add_{indice_selecao}")
                obrig = st.checkbox("Obrigatório", key=f"obrig_add_{indice_selecao}")
                in_tabela = st.checkbox("Dentro da tabela?", key=f"tabela_add_{indice_selecao}")
                linha_tabela = None
                if in_tabela:
                    linha_tabela = st.number_input("Número da linha na tabela", min_value=1, step=1, key=f"linha_add_{indice_selecao}")
                largura = st.number_input("Largura (px)", min_value=100, value=450, step=10, key=f"larg_add_{indice_selecao}")
                altura = None
                if tipo == "texto-area":
                    altura = st.number_input("Altura", min_value=50, value=100, step=10, key=f"alt_add_{indice_selecao}")
                colunas = 1
                dominios_temp = []
                if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"]:
                    colunas = st.number_input("Colunas", min_value=1, max_value=5, value=1, key=f"colunas_add_{indice_selecao}")
                    qtd_dom = st.number_input("Qtd. de Itens no Domínio", min_value=1, max_value=50, value=2, key=f"qtd_dom_add_{indice_selecao}")
                    for i in range(int(qtd_dom)):
                        val = st.text_input(f"Descrição Item {i+1}", key=f"desc_add_{indice_selecao}_{i}")
                        if val:
                            dominios_temp.append({"descricao": val, "valor": val.upper()})
                if st.button("Adicionar Campo", key=f"add_field_{indice_selecao}"):
                    campo = {
                        "titulo": titulo,
                        "descricao": titulo,
                        "tipo": tipo,
                        "obrigatorio": obrig,
                        "largura": largura,
                        "altura": altura,
                        "colunas": colunas,
                        "in_tabela": in_tabela,
                        "dominios": dominios_temp,
                        "valor": ""
                    }
                    adicionar_campo_secao(secao_atual, campo, linha_tabela)
                    st.rerun()

with aba[1]:
    st.title("Importar Arquivo de Formulário")
    uploaded_file = st.file_uploader("Escolha o arquivo XML para importar", type=["xml", "gfe"])
    if uploaded_file is not None:
        try:
            content = uploaded_file.read()
            dict_parsed = xmltodict.parse(content)
            formulario_dict = {}
            if "gxsi:formulario" in dict_parsed:
                form_data = dict_parsed["gxsi:formulario"]
                formulario_dict["nome"] = form_data.get("@nome", "")
                formulario_dict["versao"] = form_data.get("@versao", "1.0")
                formulario_dict["secoes"] = []

                elementos = form_data.get("elementos", {}).get("elemento", [])
                if not isinstance(elementos, list):
                    elementos = [elementos]

                for elem in elementos:
                    if elem.get("@gxsi:type") == "seccao":
                        sec = {
                            "titulo": elem.get("@titulo", ""),
                            "largura": int(elem.get("@largura", "500")),
                            "elementos": []
                        }
                        sec_elementos = elem.get("elementos", {}).get("elemento", [])
                        if not isinstance(sec_elementos, list):
                            sec_elementos = [sec_elementos]
                        for se in sec_elementos:
                            tipo = se.get("@gxsi:type")
                            if tipo == "tabela":
                                linhas = se.get("linhas", {}).get("linha", [])
                                if not isinstance(linhas, list):
                                    linhas = [linhas]
                                tabela = []
                                for linha in linhas:
                                    celulas = linha.get("celulas", {}).get("celula", [])
                                    if not isinstance(celulas, list):
                                        celulas = [celulas]
                                    linha_lista = []
                                    for cel in celulas:
                                        elementos_cel = cel.get("elementos", {}).get("elemento", [])
                                        if not isinstance(elementos_cel, list):
                                            elementos_cel = [elementos_cel]
                                        campos = []
                                        for c in elementos_cel:
                                            c_info = {
                                                "tipo": c.get("@gxsi:type", "texto"),
                                                "titulo": c.get("@titulo", ""),
                                                "descricao": c.get("@descricao", ""),
                                                "obrigatorio": c.get("@obrigatorio", "false") == "true",
                                                "largura": int(c.get("@largura", "450")),
                                                "altura": int(c.get("@altura", "0")) if c.get("@altura") else None,
                                                "colunas": int(c.get("@colunas", "1"))
                                            }
                                            campos.append(c_info)
                                        linha_lista.append(campos)
                                    tabela.append(linha_lista)
                                sec["elementos"].append({"tipo_elemento": "tabela", "tabela": tabela})
                            else:
                                c_info = {
                                    "tipo": tipo,
                                    "titulo": se.get("@titulo", ""),
                                    "descricao": se.get("@descricao", ""),
                                    "obrigatorio": se.get("@obrigatorio", "false") == "true",
                                    "largura": int(se.get("@largura", "450")),
                                    "altura": int(se.get("@altura", "0")) if se.get("@altura") else None,
                                    "colunas": int(se.get("@colunas", "1")),
                                    "in_tabela": False,
                                    "dominios": []
                                }
                                sec["elementos"].append({"tipo_elemento": "campo", "campo": c_info})
                        formulario_dict["secoes"].append(sec)
                st.session_state.formulario = formulario_dict
                st.success("Arquivo importado com sucesso!")
            else:
                st.error("Arquivo não contém estrutura válida de formulário.")
        except Exception as e:
            st.error(f"Erro ao importar arquivo: {str(e)}")

# Funções auxiliares
def reorder_elementos(elementos, idx, direcao):
    novo_idx = idx + direcao
    if novo_idx < 0 or novo_idx >= len(elementos):
        return elementos
    elementos[idx], elementos[novo_idx] = elementos[novo_idx], elementos[idx]
    return elementos
