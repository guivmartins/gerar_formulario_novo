import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom

st.set_page_config(page_title="Construtor de Formulários Completo 8.0", layout="wide")

# Estado inicial
if "formulario" not in st.session_state:
    st.session_state.formulario = {"nome": "", "versao": "1.0", "secoes": [], "dominios": []}
if "nova_secao" not in st.session_state:
    st.session_state.nova_secao = {"titulo": "", "largura": 500, "elementos": []}
if "editing" not in st.session_state:
    st.session_state.editing = None  # {"s": s_idx, "i": i}

TIPOS_ELEMENTOS = [
    "texto", "texto-area", "data", "moeda", "cpf", "cnpj", "email",
    "telefone", "check", "comboBox", "comboFiltro", "grupoRadio",
    "grupoCheck", "paragrafo", "rotulo"
]
LIST_TYPES = {"comboBox", "comboFiltro", "grupoRadio", "grupoCheck"}

# =================== Funções NOVAS: XML -> Estrutura interna ===================

def _localname(tag: str) -> str:
    return tag.split('}')[-1] if '}' in tag else tag

def _get_type_attr(el: ET.Element) -> str:
    for k, v in el.attrib.items():
        if k.endswith("type"):
            return v
    return ""

def _to_bool(v: str) -> bool:
    return str(v).strip().lower() in ("true", "1", "yes")

def _parse_dominios(root: ET.Element) -> dict:
    dom_map = {}
    for child in root:
        if _localname(child.tag) == "dominios":
            for dom in child:
                if _localname(dom.tag) != "dominio":
                    continue
                chave = dom.attrib.get("chave", "")
                itens = []
                for sub in dom:
                    if _localname(sub.tag) != "itens":
                        continue
                    for it in sub:
                        if _localname(it.tag) != "item":
                            continue
                        itens.append({
                            "descricao": it.attrib.get("descricao", ""),
                            "valor": it.attrib.get("valor", "")
                        })
                if chave:
                    dom_map[chave] = itens
    return dom_map

def _parse_campo(el: ET.Element, dom_map: dict) -> dict:
    tipo = _get_type_attr(el) or el.attrib.get("tipo", "texto")
    largura = int(el.attrib.get("largura", "450") or 450)

    if tipo in ("paragrafo", "rotulo"):
        return {
            "tipo": tipo,
            "valor": el.attrib.get("valor", el.attrib.get("descricao", el.attrib.get("titulo", ""))),
            "largura": largura,
            "obrigatorio": False,
            "in_tabela": False,
        }

    if tipo in LIST_TYPES:
        titulo = el.attrib.get("titulo", "")
        desc = el.attrib.get("descricao", titulo)
        obrig = _to_bool(el.attrib.get("obrigatorio", "false"))
        colunas = int(el.attrib.get("colunas", "1") or 1)
        chave_dom = el.attrib.get("dominio", "")
        dominios = dom_map.get(chave_dom, [])
        return {
            "tipo": tipo,
            "titulo": titulo,
            "descricao": desc,
            "obrigatorio": obrig,
            "largura": largura,
            "colunas": colunas,
            "dominios": dominios,
            "dominio_chave": chave_dom,
            "in_tabela": False,
            "valor": ""
        }

    titulo = el.attrib.get("titulo", "")
    desc = el.attrib.get("descricao", titulo)
    obrig = _to_bool(el.attrib.get("obrigatorio", "false"))
    campo = {
        "tipo": tipo,
        "titulo": titulo,
        "descricao": desc,
        "obrigatorio": obrig,
        "largura": largura,
        "in_tabela": False,
        "valor": ""
    }
    if tipo == "texto-area":
        if "altura" in el.attrib:
            try:
                campo["altura"] = int(el.attrib.get("altura", "100") or 100)
            except:
                campo["altura"] = 100
    return campo

def _parse_tabela(tab_el: ET.Element, dom_map: dict):
    tabela = []
    for child in tab_el:
        if _localname(child.tag) != "linhas":
            continue
        for linha in child:
            if _localname(linha.tag) != "linha":
                continue
            linha_list = []
            for celulas in linha:
                if _localname(celulas.tag) != "celulas":
                    continue
                for cel in celulas:
                    if _localname(cel.tag) != "celula":
                        continue
                    campos = []
                    for elems in cel:
                        if _localname(elems.tag) != "elementos":
                            continue
                        for el in elems:
                            if _localname(el.tag) != "elemento":
                                continue
                            campos.append(_parse_campo(el, dom_map))
                    linha_list.append(campos)
            tabela.append(linha_list)
    return tabela

def _parse_secao(sec_el: ET.Element, dom_map: dict) -> dict:
    sec = {
        "titulo": sec_el.attrib.get("titulo", ""),
        "largura": int(sec_el.attrib.get("largura", "500") or 500),
        "elementos": []
    }
    for child in sec_el:
        if _localname(child.tag) != "elementos":
            continue
        for el in child:
            if _localname(el.tag) != "elemento":
                continue
            tipo_el = _get_type_attr(el)
            if tipo_el == "tabela":
                tabela = _parse_tabela(el, dom_map)
                sec["elementos"].append({"tipo_elemento": "tabela", "tabela": tabela})
            else:
                campo = _parse_campo(el, dom_map)
                sec["elementos"].append({"tipo_elemento": "campo", "campo": campo})
    return sec

def parse_formulario_from_xml(source) -> dict:
    tree = ET.parse(source)
    root = tree.getroot()
    dom_map = _parse_dominios(root)

    nome = root.attrib.get("nome", "")
    versao = root.attrib.get("versao", "1.0")

    secoes = []
    for child in root:
        if _localname(child.tag) != "elementos":
            continue
        for el in child:
            if _localname(el.tag) != "elemento":
                continue
            tipo = _get_type_attr(el)
            if tipo == "seccao":
                secoes.append(_parse_secao(el, dom_map))

    return {
        "nome": nome,
        "versao": versao,
        "secoes": secoes,
        "dominios": []
    }

# =================== Funções EXISTENTES: geração e UI ===================

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

    dom_adicionados = set()
    dominios_global = ET.Element("dominios")

    def ensure_dominio(chave_dom: str, itens: list):
        if not chave_dom or chave_dom in dom_adicionados:
            return
        dominio_el = ET.SubElement(dominios_global, "dominio", {
            "gxsi:type": "dominioEstatico",
            "chave": chave_dom
        })
        itens_el = ET.SubElement(dominio_el, "itens")
        for d in itens or []:
            ET.SubElement(itens_el, "item", {
                "gxsi:type": "dominioItemValor",
                "descricao": d.get("descricao", ""),
                "valor": d.get("valor", "")
            })
        dom_adicionados.add(chave_dom)

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

                if tipo in LIST_TYPES:
                    chave_dom = campo.get("dominio_chave") or titulo.replace(" ", "")[:20].upper()
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
                    ensure_dominio(chave_dom, campo.get("dominios", []))
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

                            if tipo in LIST_TYPES:
                                chave_dom = campo.get("dominio_chave") or titulo.replace(" ", "")[:20].upper()
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
                                ensure_dominio(chave_dom, campo.get("dominios", []))
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
                        st.checkbox(dom.get("descricao", ""), key=f"{key_prev}_{i}")
                elif tipo in ["comboBox", "comboFiltro"]:
                    st.multiselect(campo.get("titulo", ""), [d.get("descricao", "") for d in campo.get("dominios", [])], key=key_prev)
                elif tipo == "grupoRadio":
                    st.radio(campo.get("titulo", ""), [d.get("descricao", "") for d in campo.get("dominios", [])], key=key_prev)
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
                                        st.checkbox(dom.get("descricao", ""), key=f"{key_prev}_{i}")
                                elif tipo in ["comboBox", "comboFiltro"]:
                                    st.multiselect(campo.get("titulo", ""), [d.get("descricao", "") for d in campo.get("dominios", [])], key=key_prev)
                                elif tipo == "grupoRadio":
                                    st.radio(campo.get("titulo", ""), [d.get("descricao", "") for d in campo.get("dominios", [])], key=key_prev)
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

def edit_campo_ui(campo: dict, key_prefix: str):
    campo["titulo"] = st.text_input("Título", value=campo.get("titulo", ""), key=f"{key_prefix}_titulo")
    campo["descricao"] = st.text_input("Descrição", value=campo.get("descricao", campo.get("titulo","")), key=f"{key_prefix}_desc")
    campo["obrigatorio"] = st.checkbox("Obrigatório", value=bool(campo.get("obrigatorio", False)), key=f"{key_prefix}_obrig")
    campo["largura"] = st.number_input("Largura (px)", min_value=100, value=int(campo.get("largura", 450)), step=10, key=f"{key_prefix}_larg")
    if campo.get("tipo") == "texto-area":
        campo["altura"] = st.number_input("Altura", min_value=50, value=int(campo.get("altura") or 100), step=10, key=f"{key_prefix}_alt")
    if campo.get("tipo") in LIST_TYPES:
        campo["colunas"] = st.number_input("Colunas", min_value=1, max_value=5, value=int(campo.get("colunas", 1)), key=f"{key_prefix}_cols")
        dominios = campo.get("dominios") or []
        qtd = st.number_input("Qtd. de Itens no Domínio", min_value=0, max_value=100, value=len(dominios), key=f"{key_prefix}_dom_qtd")
        if len(dominios) < qtd:
            dominios.extend([{"descricao": "", "valor": ""} for _ in range(qtd - len(dominios))])
        elif len(dominios) > qtd:
            dominios = dominios[:qtd]
        for i in range(qtd):
            c1, c2 = st.columns(2)
            with c1:
                dominios[i]["descricao"] = st.text_input(f"Descrição {i+1}", value=dominios[i].get("descricao",""), key=f"{key_prefix}_dom_desc_{i}")
            with c2:
                dominios[i]["valor"] = st.text_input(f"Valor {i+1}", value=dominios[i].get("valor",""), key=f"{key_prefix}_dom_val_{i}")
        campo["dominios"] = dominios

# =================== Layout principal com colunas ===================
# col_esq: Construtor + XML abaixo; col_dir: Prévia do formulário
col_esq, col_dir = st.columns([3, 2], gap="medium")

with col_esq:
    st.title("Construtor de Formulários Completo 8.0")

    # --- Importar XML/.GFE para edição (AGORA LOGO ABAIXO DO TÍTULO) ---
    with st.expander("📥 Importar XML/.GFE", expanded=False):
        up = st.file_uploader(
            "Selecione o arquivo",
            type=["xml", "gfe"],
            accept_multiple_files=False,
            key="upload_xml"
        )
        if up is not None:
            if st.button("Carregar", key="btn_import_xml"):
                try:
                    form = parse_formulario_from_xml(up)  # lê UploadedFile (file-like) diretamente
                    st.session_state.formulario = form
                    st.session_state.nova_secao = {"titulo": "", "largura": 500, "elementos": []}
                    st.session_state.editing = None
                    st.success(f"Importado: {up.name}")
                    st.rerun()
                except ET.ParseError as e:
                    st.error(f"XML inválido: {e}")
                except Exception as e:
                    st.error(f"Falha ao importar: {e}")

    # Campo de nome do formulário permanece abaixo do import
    st.session_state.formulario["nome"] = st.text_input(
        "Nome do Formulário",
        st.session_state.formulario.get("nome","")
    )
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
        with st.expander(f"Seção: {sec.get('titulo','(sem título)')}", expanded=False):
            sec["titulo"] = st.text_input("Título da Seção (editar)", value=sec.get("titulo",""), key=f"sec_tit_{s_idx}")
            sec["largura"] = st.number_input("Largura da Seção (editar)", min_value=100, value=int(sec.get("largura",500)), step=10, key=f"sec_larg_{s_idx}")
            t1, t2 = st.columns([1,1])
            with t1:
                if st.button("Salvar Seção", key=f"save_sec_{s_idx}"):
                    st.rerun()
            with t2:
                if st.button("Excluir Seção", key=f"del_sec_{s_idx}"):
                    st.session_state.formulario["secoes"].pop(s_idx)
                    st.rerun()

            st.markdown("### Elementos (ordem e edição)")
            elementos = sec.get("elementos", [])
            for i, item in enumerate(list(elementos)):
                c1, c2, c3, c4 = st.columns([1,1,8,2])
                with c1:
                    if st.button("⬆️", key=f"up_{s_idx}_{i}"):
                        sec["elementos"] = reorder_elementos(elementos, i, -1)
                        st.rerun()
                with c2:
                    if st.button("⬇️", key=f"down_{s_idx}_{i}"):
                        sec["elementos"] = reorder_elementos(elementos, i, 1)
                        st.rerun()
                with c3:
                    if item["tipo_elemento"] == "campo":
                        st.text(f"Campo: {item['campo'].get('titulo', '')} ({item['campo'].get('tipo','')})")
                    else:
                        st.markdown("Tabela:")
                        for l_idx, linha in enumerate(item["tabela"]):
                            cel_textos = []
                            for c_idx, celula in enumerate(linha):
                                titulos = ", ".join([c.get("titulo", "") for c in celula])
                                cel_textos.append(f"Celula {c_idx+1}: {titulos}")
                            st.text(f"Linha {l_idx+1}: " + " | ".join(cel_textos))
                with c4:
                    if st.button("✏️ Editar", key=f"edit_{s_idx}_{i}"):
                        st.session_state.editing = {"s": s_idx, "i": i}
                        st.rerun()
                    if st.button("❌", key=f"del_{s_idx}_{i}"):
                        elementos.pop(i)
                        st.rerun()

                if st.session_state.editing and st.session_state.editing.get("s") == s_idx and st.session_state.editing.get("i") == i:
                    if item["tipo_elemento"] == "campo":
                        campo = item["campo"]
                        st.write("Editar campo")
                        edit_campo_ui(campo, key_prefix=f"editcampo_{s_idx}_{i}")
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("Salvar", key=f"save_campo_{s_idx}_{i}"):
                                st.session_state.editing = None
                                st.rerun()
                        with b2:
                            if st.button("Cancelar", key=f"cancel_campo_{s_idx}_{i}"):
                                st.session_state.editing = None
                                st.rerun()
                    else:
                        st.write("Editar tabela")
                        tabela = item["tabela"]
                        for l_idx, linha in enumerate(tabela):
                            st.markdown(f"— Linha {l_idx+1}")
                            for c_idx, celula in enumerate(linha):
                                with st.expander(f"Celula {c_idx+1}", expanded=False):
                                    for f_idx, campo in enumerate(celula):
                                        st.markdown(f"Campo {f_idx+1} — {campo.get('tipo','')}")
                                        edit_campo_ui(campo, key_prefix=f"edittab_{s_idx}_{i}_{l_idx}_{c_idx}_{f_idx}")
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("Salvar tabela", key=f"save_tab_{s_idx}_{i}"):
                                st.session_state.editing = None
                                st.rerun()
                        with b2:
                            if st.button("Cancelar", key=f"cancel_tab_{s_idx}_{i}"):
                                st.session_state.editing = None
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
            linha_tabela = st.number_input("Número da linha na tabela", min_value=1, step=1, key=f"linha_add_{indice_selecao}") if in_tabela else None
            largura = st.number_input("Largura (px)", min_value=100, value=450, step=10, key=f"larg_add_{indice_selecao}")
            altura = st.number_input("Altura", min_value=50, value=100, step=10, key=f"alt_add_{indice_selecao}") if tipo == "texto-area" else None
            colunas = 1
            dominios_temp = []
            if tipo in LIST_TYPES:
                colunas = st.number_input("Colunas", min_value=1, max_value=5, value=1, key=f"colunas_add_{indice_selecao}")
                qtd_dom = st.number_input("Qtd. de Itens no Domínio", min_value=0, max_value=50, value=2, key=f"qtd_dom_add_{indice_selecao}")
                for i in range(int(qtd_dom)):
                    d1, d2 = st.columns(2)
                    with d1:
                        desc = st.text_input(f"Descrição Item {i+1}", key=f"desc_add_{indice_selecao}_{i}")
                    with d2:
                        val = st.text_input(f"Valor Item {i+1}", key=f"val_add_{indice_selecao}_{i}")
                    if desc or val:
                        dominios_temp.append({"descricao": desc, "valor": val or (desc.upper() if desc else "")})
            if st.button("Adicionar Campo", key=f"add_field_{indice_selecao}"):
                campo = {
                    "titulo": titulo, "descricao": titulo, "tipo": tipo, "obrigatorio": obrig,
                    "largura": largura, "altura": altura, "colunas": colunas, "in_tabela": in_tabela,
                    "dominios": dominios_temp, "valor": ""
                }
                adicionar_campo_secao(secao_atual, campo, linha_tabela)
                st.rerun()

    # XML PREVIEW abaixo do construtor (coluna esquerda)
    st.markdown("---")
    st.subheader("📑 Pré-visualização XML")
    st.code(gerar_xml(st.session_state.formulario), language="xml")

with col_dir:
    # PRÉVIA DO FORMULÁRIO (coluna direita)
    preview_formulario(st.session_state.formulario, context_key="builder")
