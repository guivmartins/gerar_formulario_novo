import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import xmltodict

st.set_page_config(page_title="Construtor de Formulários Completo 8.0", layout="wide")

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

    largura_base = 500
    if formulario.get("secoes"):
        largura_base = int(formulario["secoes"][0].get("largura", 500))
    total_cols = 12

    for s_idx, sec in enumerate(formulario.get("secoes", [])):
        st.markdown(f"### {sec.get('titulo')}")
        elementos_lista = sec.get("elementos", [])
        for idx, item in enumerate(elementos_lista):
            campo = item.get("campo") if item["tipo_elemento"] == "campo" else None
            largura_elem = int(campo.get("largura", 450)) if campo else 450
            col_w_ratio = largura_elem / largura_base
            col_w = max(1, min(int(col_w_ratio * total_cols), total_cols))

            if col_w == total_cols:
                cols_elem = st.columns([total_cols])
            else:
                cols_elem = st.columns([col_w, total_cols - col_w])

            with cols_elem[0]:
                if item["tipo_elemento"] == "campo" and campo:
                    key_prev = f"prev_{context_key}_{s_idx}_{idx}_{sec.get('titulo')}_{campo.get('titulo')}"
                    tipo = campo.get("tipo")
                    if tipo == "texto":
                        st.text_input(campo.get("titulo", ""), key=key_prev)
                    elif tipo == "texto-area":
                        st.text_area(campo.get("titulo", ""), height=campo.get("altura", 100), key=key_prev)
                    elif tipo == "data":
                        st.date_input(campo.get("titulo", ""), key=key_prev)
                    elif tipo == "grupoCheck":
                        st.markdown(f"**{campo.get('titulo', '')}**")
                        dominios = campo.get("dominios", [])
                        colunas = max(1, campo.get("colunas", 1))
                        cols_gc = st.columns(colunas)
                        for idx_dom, dom in enumerate(dominios):
                            col_gc = cols_gc[idx_dom % colunas]
                            with col_gc:
                                st.checkbox(dom.get("descricao", ""), key=f"{key_prev}_{idx_dom}")
                    elif tipo == "grupoRadio":
                        st.markdown(f"**{campo.get('titulo', '')}**")
                        dominios = campo.get("dominios", [])
                        colunas = max(1, campo.get("colunas", 1))
                        options = [d.get("descricao", "") for d in dominios]
                        chunked = [options[i::colunas] for i in range(colunas)]
                        cols_gr = st.columns(colunas)
                        for opt_list, col_gr in zip(chunked, cols_gr):
                            with col_gr:
                                for radio_val in opt_list:
                                    st.radio("", [radio_val], key=f"{key_prev}_{radio_val}")
                    elif tipo in ["comboBox", "comboFiltro"]:
                        st.multiselect(campo.get("titulo", ""), [d.get("descricao", "") for d in campo.get("dominios", [])], key=key_prev)
                    elif tipo == "check":
                        st.checkbox(campo.get("titulo", ""), key=key_prev)
                    elif tipo == "rotulo":
                        st.markdown(f"**{campo.get('titulo', '')}**")
                    elif tipo == "paragrafo":
                        conteudo = campo.get("titulo", "")
                        conteudo = str(conteudo).replace("\\n", "\n")
                        st.markdown(conteudo)
                elif item["tipo_elemento"] == "tabela":
                    tabela = item["tabela"]
                    st.markdown("**Tabela:**")
                    for linha_idx, linha in enumerate(tabela):
                        cols_linha = st.columns(len(linha))
                        for c_idx, celula in enumerate(linha):
                            with cols_linha[c_idx]:
                                for c_idx2, campo_tab in enumerate(celula):
                                    largura_elem_tab = int(campo_tab.get("largura", 450))
                                    col_w_ratio_tab = largura_elem_tab / largura_base
                                    col_w_tab = max(1, min(int(col_w_ratio_tab * total_cols), total_cols))

                                    if col_w_tab == total_cols:
                                        cols_elem_tab = st.columns([total_cols])
                                    else:
                                        cols_elem_tab = st.columns([col_w_tab, total_cols - col_w_tab])
                                    with cols_elem_tab[0]:
                                        tipo_tab = campo_tab.get("tipo")
                                        key_prev = f"prev_{context_key}_{s_idx}_t{idx}_l{linha_idx}_c{c_idx}_f{c_idx2}_{sec.get('titulo')}_{campo_tab.get('titulo')}"
                                        if tipo_tab == "texto":
                                            st.text_input(campo_tab.get("titulo", ""), key=key_prev)
                                        elif tipo_tab == "texto-area":
                                            st.text_area(campo_tab.get("titulo", ""), height=campo_tab.get("altura", 100), key=key_prev)
                                        elif tipo_tab == "data":
                                            st.date_input(campo_tab.get("titulo", ""), key=key_prev)
                                        elif tipo_tab == "grupoCheck":
                                            st.markdown(f"**{campo_tab.get('titulo', '')}**")
                                            dominios = campo_tab.get("dominios", [])
                                            colunas = max(1, campo_tab.get("colunas", 1))
                                            cols_gc = st.columns(colunas)
                                            for idx_dom, dom in enumerate(dominios):
                                                col_gc = cols_gc[idx_dom % colunas]
                                                with col_gc:
                                                    st.checkbox(dom.get("descricao", ""), key=f"{key_prev}_{idx_dom}")
                                        elif tipo_tab == "grupoRadio":
                                            st.markdown(f"**{campo_tab.get('titulo', '')}**")
                                            dominios = campo_tab.get("dominios", [])
                                            colunas = max(1, campo_tab.get("colunas", 1))
                                            options = [d.get("descricao", "") for d in dominios]
                                            chunked = [options[i::colunas] for i in range(colunas)]
                                            cols_gr = st.columns(colunas)
                                            for opt_list, col_gr in zip(chunked, cols_gr):
                                                with col_gr:
                                                    for radio_val in opt_list:
                                                        st.radio("", [radio_val], key=f"{key_prev}_{radio_val}")
                                        elif tipo_tab in ["comboBox", "comboFiltro"]:
                                            st.multiselect(campo_tab.get("titulo", ""), [d.get("descricao", "") for d in campo_tab.get("dominios", [])], key=key_prev)
                                        elif tipo_tab == "check":
                                            st.checkbox(campo_tab.get("titulo", ""), key=key_prev)
                                        elif tipo_tab == "rotulo":
                                            st.markdown(f"**{campo_tab.get('titulo', '')}**")
                                        elif tipo_tab == "paragrafo":
                                            conteudo = campo_tab.get("titulo", "")
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

aba = st.tabs(["Construtor", "Importar arquivo"])

with aba[0]:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.title("Construtor de Formulários Completo 8.0")
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
