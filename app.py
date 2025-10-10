import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom

st.set_page_config(page_title="Construtor de Formulários 7.3", layout="wide")

# Inicialização do estado para controle de tabela/linha aberta
if "formulario" not in st.session_state:
    st.session_state.formulario = {
        "nome": "",
        "versao": "1.0",
        "secoes": [],
        "dominios": []
    }
if "nova_secao" not in st.session_state:
    st.session_state.nova_secao = {"titulo": "", "largura": 500, "campos": []}

if "tabela_aberta" not in st.session_state:
    st.session_state.tabela_aberta = False
if "linha_aberta" not in st.session_state:
    st.session_state.linha_aberta = False
if "tabela_atual" not in st.session_state:
    # estrutura: lista de linhas, cada linha lista de células, cada célula lista de campos
    st.session_state.tabela_atual = []

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

        # Percorrer campos na seção, checando se tabela está fechada
        # Para suporte à nova estrutura de tabelas:
        campos = sec.get("campos", [])

        # Campos normais sem tabela
        campos_sem_tabela = []

        # Campos e estruturas de tabela — caso tabela esteja presente, prontificar aninhamento conforme estrutura
        # Nosso formulário usa estrutura 'tabelas' na seção (se houver)
        tabelas = sec.get("tabelas", [])  # hipótese: armazenar as tabelas aqui

        # Se houver tabelas, gera primeiro elas tradicionalmente
        if tabelas:
            for tabela in tabelas:
                tabela_el = ET.SubElement(subelems, "elemento", {"gxsi:type": "tabela"})
                linhas_tag = ET.SubElement(tabela_el, "linhas")
                for linha in tabela:
                    linha_tag = ET.SubElement(linhas_tag, "linha")
                    celulas_tag = ET.SubElement(linha_tag, "celulas")
                    for celula in linha:
                        # celula é lista de campos
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
        # Acrescenta os campos que não são parte da tabela
        for campo in campos:
            if not campo.get("in_tabela", False):
                campos_sem_tabela.append(campo)
        for campo in campos_sem_tabela:
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

def _ler_dominios(root: ET.Element):
    dominios_map = {}
    dominios_el = root.find("dominios")
    if dominios_el is not None:
        for dominio_el in dominios_el.findall("dominio"):
            chave = dominio_el.attrib.get("chave")
            itens = []
            itens_el = dominio_el.find("itens")
            if itens_el is not None:
                for item_el in itens_el.findall("item"):
                    itens.append({
                        "descricao": item_el.attrib.get("descricao", ""),
                        "valor": item_el.attrib.get("valor", "")
                    })
            if chave:
                dominios_map[chave] = itens
    return dominios_map

def _ler_itens_dominio(dominios_map, chave):
    return dominios_map.get(chave, []) if chave else []

def _buscar_campos_rec(elementos_node: ET.Element, dominios_map: dict):
    campos = []
    if elementos_node is None:
        return campos
    for el in elementos_node.findall("elemento"):
        tipo = el.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
        if tipo == "tabela":
            linhas = el.find("linhas")
            if linhas is not None:
                for linha in linhas.findall("linha"):
                    celulas = linha.find("celulas")
                    if celulas is not None:
                        for celula in celulas.findall("celula"):
                            sub = celula.find("elementos")
                            campos.extend(_buscar_campos_rec(sub, dominios_map))
        else:
            dominio_chave = el.attrib.get("dominio")
            campos.append({
                "tipo": tipo or "texto",
                "titulo": el.attrib.get("titulo", ""),
                "descricao": el.attrib.get("descricao", el.attrib.get("titulo", "")),
                "obrigatorio": el.attrib.get("obrigatorio", "false").lower() == "true",
                "largura": int(el.attrib.get("largura", 450)) if el.attrib.get("largura") else 450,
                "altura": int(el.attrib.get("altura", 100)) if tipo == "texto-area" and el.attrib.get("altura") else None,
                "colunas": int(el.attrib.get("colunas", 1)) if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] and el.attrib.get("colunas") else 1,
                "in_tabela": False,
                "dominios": _ler_itens_dominio(dominios_map, dominio_chave),
                "valor": el.attrib.get("valor", "")
            })
    return campos

def preview_formulario(formulario: dict, context_key: str = "main"):
    st.header("📋 Pré-visualização do Formulário")
    st.subheader(formulario.get("nome", ""))
    for s_idx, sec in enumerate(formulario.get("secoes", [])):
        st.markdown(f"### {sec.get('titulo')}")
        tabela_aberta = False

        tabelas = sec.get("tabelas", [])
        # mostra o conteúdo tabelado primeiro
        for tabela_idx, tabela in enumerate(tabelas):
            st.markdown(f"**Tabela {tabela_idx+1}**")
            for linha_idx, linha in enumerate(tabela):
                cols = st.columns(len(linha))
                for c_idx, celula in enumerate(linha):
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
        # depois mostra campos que não fazem parte de tabelas
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
                conteudo = campo.get("valor") or campo.get("descricao") or campo.get("titulo") or ""
                st.markdown(f"**{conteudo}**")
            elif tipo == "paragrafo":
                conteudo = campo.get("valor") or campo.get("descricao") or campo.get("titulo") or ""
                conteudo = str(conteudo).replace("\\n", "\n")
                st.markdown(conteudo)

def mover_item(lista, idx, direcao):
    novo = idx + direcao
    if 0 <= novo < len(lista):
        lista[idx], lista[novo] = lista[novo], lista[idx]
        return True
    return False

def ordenar_campos_por_drag(secao: dict, sec_index: int, context_key: str) -> None:
    campos = secao.get('campos', [])
    if not campos:
        st.info("Nenhum campo para reordenar.")
        return
    st.markdown("Reordene manualmente os campos abaixo usando as setas:")
    for i, c in enumerate(secao["campos"]):
        label = f"{c.get('tipo','texto')} - {c.get('titulo','')}"
        colA, colB, colC = st.columns([6,1,1])
        with colA:
            st.caption(f"{i+1}. {label}")
        with colB:
            if st.button("↑", key=f"up_{context_key}_{sec_index}_{i}"):
                if mover_item(secao["campos"], i, -1):
                    st.rerun()
        with colC:
            if st.button("↓", key=f"down_{context_key}_{sec_index}_{i}"):
                if mover_item(secao["campos"], i, +1):
                    st.rerun()

def adicionar_campo_secao(secao, campo):
    if campo.get("in_tabela"):
        # Se tabela não aberta, abrir tabela + linha
        if not st.session_state.tabela_aberta:
            st.session_state.tabela_atual = []
            st.session_state.tabela_aberta = True
            st.session_state.linha_aberta = True
            st.session_state.tabela_atual.append([])  # primeira linha vazia
            st.success("Tabela aberta automaticamente.")
        if st.session_state.linha_aberta:
            linha_atual = st.session_state.tabela_atual[-1]
            # A célula 0 (primeira) e 1 (segunda) são as únicas previstas para linha (2 células)
            # Cada célula mantém uma lista de campos
            # Se primeira linha não tiver 2 células, criá-las
            while len(linha_atual) < 2:
                linha_atual.append([])
            # tenta adicionar no primeira ou segunda célula que tenha menos de 1 campo
            if len(linha_atual[0]) < 1:
                linha_atual[0].append(campo)
                st.success(f"Campo '{campo.get('titulo')}' adicionado na linha atual, primeira célula.")
            elif len(linha_atual[1]) < 1:
                linha_atual[1].append(campo)
                st.success(f"Campo '{campo.get('titulo')}' adicionado na linha atual, segunda célula.")
            else:
                st.warning("Linha atual está cheia (2 células com 1 campo). Por favor, finalize a linha para adicionar mais campos.")
        else:
            # Linha não aberta: criar linha nova
            st.session_state.linha_aberta = True
            st.session_state.tabela_atual.append([[campo]])
            st.success("Nova linha criada e campo adicionado na primeira célula.")
    else:
        # Campo fora da tabela
        # Se tabela aberta, fecha tabela automaticamente antes de adicionar campo isolado
        if st.session_state.tabela_aberta:
            finalizar_linha()
            finalizar_tabela(secao)
        # adiciona campo normal na lista de campos da seção
        secao["campos"].append(campo)
        st.success(f"Campo '{campo.get('titulo')}' adicionado fora da tabela.")

def finalizar_linha():
    if st.session_state.linha_aberta:
        st.session_state.linha_aberta = False
        st.success("Linha atual finalizada.")
    else:
        st.warning("Nenhuma linha aberta para finalizar.")

def finalizar_tabela(secao):
    if st.session_state.tabela_aberta:
        # Adicionar tabela atual na seção
        if "tabelas" not in secao:
            secao["tabelas"] = []
        secao["tabelas"].append(st.session_state.tabela_atual)
        st.session_state.tabela_aberta = False
        st.session_state.linha_aberta = False
        st.session_state.tabela_atual = []
        st.success("Tabela finalizada e adicionada à seção.")
    else:
        st.warning("Nenhuma tabela aberta para finalizar.")

aba = st.tabs(["Construtor", "Importar arquivo"])

with aba[0]:
    col1, col2 = st.columns(2)
    with col1:
        st.title("Construtor de Formulários 7.3")
        st.session_state.formulario["nome"] = st.text_input("Nome do Formulário", st.session_state.formulario["nome"])
        st.markdown("---")
        with st.expander("➕ Adicionar Seção", expanded=True):
            st.session_state.nova_secao["titulo"] = st.text_input("Título da Seção", st.session_state.nova_secao["titulo"])
            st.session_state.nova_secao["largura"] = st.number_input("Largura da Seção", min_value=100, value=st.session_state.nova_secao["largura"], step=10)
            if st.button("Salvar Seção"):
                if st.session_state.nova_secao["titulo"]:
                    st.session_state.formulario["secoes"].append(st.session_state.nova_secao.copy())
                    st.session_state.nova_secao = {"titulo": "", "largura": 500, "campos": []}
                    st.rerun()
        st.markdown("---")
        for s_idx, sec in enumerate(st.session_state.formulario.get("secoes", [])):
            with st.expander(f"📁 Seção: {sec.get('titulo','(sem título)')}", expanded=False):
                st.write(f"**Largura:** {sec.get('largura', 500)}")
                if st.button(f"🗑️ Excluir Seção", key=f"del_sec_{s_idx}"):
                    st.session_state.formulario["secoes"].pop(s_idx)
                    st.rerun()
                with st.expander("🔀 Reordenar campos", expanded=False):
                    ordenar_campos_por_drag(sec, s_idx, context_key="builder")
                st.markdown("### Campos e Tabelas")
                # Mostrar campos sem tabela
                for c_idx, campo in enumerate(sec.get("campos", [])):
                    st.text(f"{campo.get('tipo')} - {campo.get('titulo')}")
                    if st.button("Excluir Campo", key=f"del_field_{s_idx}_{c_idx}"):
                        st.session_state.formulario["secoes"][s_idx]["campos"].pop(c_idx)
                        st.rerun()
                # Mostrar tabelas atuais na seção
                if "tabelas" in sec:
                    for t_idx, tabela in enumerate(sec["tabelas"]):
                        st.markdown(f"**Tabela {t_idx+1}:**")
                        for l_idx, linha in enumerate(tabela):
                            cel_texts = []
                            for c_idx, celula in enumerate(linha):
                                titulos = ", ".join([c.get("titulo", "") for c in celula])
                                cel_texts.append(f"Celula {c_idx+1}: {titulos}")
                            st.text(f"Linha {l_idx+1}: " + " | ".join(cel_texts))
                # Controle para adicionar campos
        if st.session_state.formulario.get("secoes"):
            secao_opcoes = [sec.get("titulo", f"Seção {i}") for i, sec in enumerate(st.session_state.formulario["secoes"])]
            indice_selecao = st.selectbox("Selecione a Seção para adicionar um campo", options=range(len(secao_opcoes)), format_func=lambda i: secao_opcoes[i])

            secao_atual = st.session_state.formulario["secoes"][indice_selecao]

            with st.expander(f"➕ Adicionar Campos à seção: {secao_atual.get('titulo','')}", expanded=True):
                tipo = st.selectbox("Tipo do Campo", TIPOS_ELEMENTOS, key=f"type_add_{indice_selecao}")
                titulo = st.text_input("Título do Campo", key=f"title_add_{indice_selecao}")
                obrig = st.checkbox("Obrigatório", key=f"obrig_add_{indice_selecao}")
                in_tabela = st.checkbox("Dentro da tabela?", key=f"tabela_add_{indice_selecao}")
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
                    adicionar_campo_secao(secao_atual, campo)
                    st.rerun()

            # Botões para controle de linha e tabela
            if st.button("Finalizar Linha", key="btn_finalizar_linha"):
                finalizar_linha()
            if st.button("Finalizar Tabela", key="btn_finalizar_tabela"):
                finalizar_tabela(secao_atual)

    with col2:
        preview_formulario(st.session_state.formulario, context_key="builder")
    st.markdown("---")
    st.subheader("📑 Pré-visualização XML")
    xml_preview = gerar_xml(st.session_state.formulario)
    st.code(xml_preview, language="xml")
    nome_arquivo = st.session_state.formulario.get("nome", "formulario") + ".gfe"
    st.download_button(
        label="Baixar Arquivo",
        data=xml_preview.encode("utf-8"),
        file_name=nome_arquivo,
        mime="application/xml",
        help="O arquivo .gfe é 100% compatível com XML do sistema.",
        key="download_gfe_builder"
    )

with aba[1]:
    colL, colR = st.columns(2)
    with colL:
        st.title("Importar arquivo")
        up = st.file_uploader("Selecione um arquivo XML ou GFE", type=["xml","gfe"], key="uploader_xml_editor")
        if up and st.button("Carregar"):
            try:
                content = up.getvalue().decode("utf-8")
                root = ET.fromstring(content)
                dominios_map = _ler_dominios(root)
                novo = {
                    "nome": root.attrib.get("nome", ""),
                    "versao": root.attrib.get("versao", "1.0"),
                    "secoes": [],
                    "dominios": []
                }
                elementos = root.find("elementos")
                if elementos is not None:
                    for el in elementos.findall("elemento"):
                        if el.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "seccao":
                            sec = {
                                "titulo": el.attrib.get("titulo", ""),
                                "largura": int(el.attrib.get("largura", 500)),
                                "campos": [],
                                "tabelas": []
                            }
                            sub = el.find("elementos")
                            # Para tentar carregar tabelas e campos:
                            for e in sub.findall("elemento"):
                                if e.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "tabela":
                                    linhas_xml = []
                                    linhas_el = e.find("linhas")
                                    for linha in linhas_el.findall("linha"):
                                        celulas_xml = []
                                        for celula in linha.find("celulas").findall("celula"):
                                            campos_xml = []
                                            elems = celula.find("elementos")
                                            if elems is not None:
                                                for campo_el in elems.findall("elemento"):
                                                    tipo_campo = campo_el.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "texto")
                                                    campo_dic = {
                                                        "tipo": tipo_campo,
                                                        "titulo": campo_el.attrib.get("titulo", ""),
                                                        "descricao": campo_el.attrib.get("descricao", campo_el.attrib.get("titulo", "")),
                                                        "obrigatorio": campo_el.attrib.get("obrigatorio", "false").lower() == "true",
                                                        "largura": int(campo_el.attrib.get("largura", 450)),
                                                        "altura": int(campo_el.attrib.get("altura", 100)) if tipo_campo == "texto-area" and campo_el.attrib.get("altura") else None,
                                                        "colunas": int(campo_el.attrib.get("colunas", 1)) if tipo_campo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] and campo_el.attrib.get("colunas") else 1,
                                                        "in_tabela": True,
                                                        "dominios": [],
                                                        "valor": campo_el.attrib.get("valor", "")
                                                    }
                                                    campos_xml.append(campo_dic)
                                            celulas_xml.append(campos_xml)
                                        linhas_xml.append(celulas_xml)
                                    sec["tabelas"].append(linhas_xml)
                                else:
                                    # Campo fora de tabela
                                    tipo_campo = e.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "texto")
                                    campo_dic = {
                                        "tipo": tipo_campo,
                                        "titulo": e.attrib.get("titulo", ""),
                                        "descricao": e.attrib.get("descricao", e.attrib.get("titulo", "")),
                                        "obrigatorio": e.attrib.get("obrigatorio", "false").lower() == "true",
                                        "largura": int(e.attrib.get("largura", 450)),
                                        "altura": int(e.attrib.get("altura", 100)) if tipo_campo == "texto-area" and e.attrib.get("altura") else None,
                                        "colunas": int(e.attrib.get("colunas", 1)) if tipo_campo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] and e.attrib.get("colunas") else 1,
                                        "in_tabela": False,
                                        "dominios": [],
                                        "valor": e.attrib.get("valor", "")
                                    }
                                    sec["campos"].append(campo_dic)
                            st.session_state.formulario["secoes"].append(sec)
                st.success("Arquivo carregado e pronto para edição.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar Arquivo: {e}")
        if st.session_state.formulario.get("secoes"):
            st.session_state.formulario["nome"] = st.text_input("Nome do Formulário", value=st.session_state.formulario.get("nome",""), key="imp_nome")
            st.markdown("---")
            st.subheader("Seções")
            for s_idx, sec in enumerate(st.session_state.formulario["secoes"]):
                with st.expander(f"📁 Seção: {sec.get('titulo','(sem título)')}", expanded=False):
                    st.write(f"**Largura:** {sec.get('largura', 500)}")
                    c1, c2, c3 = st.columns([3,2,1])
                    with c1:
                        novo_titulo = st.text_input("Título da Seção", value=sec.get("titulo",""), key=f"imp_sec_tit_{s_idx}")
                    with c2:
                        nova_larg = st.number_input("Largura (px)", min_value=100, value=sec.get("largura",500), step=10, key=f"imp_sec_larg_{s_idx}")
                    with c3:
                        if st.button("Salvar Seção", key=f"imp_sec_save_{s_idx}"):
                            st.session_state.formulario["secoes"][s_idx]["titulo"] = novo_titulo
                            st.session_state.formulario["secoes"][s_idx]["largura"] = nova_larg
                            st.success("Seção atualizada.")
                    if st.button(f"🗑️ Excluir Seção", key=f"imp_del_sec_{s_idx}"):
                        st.session_state.formulario["secoes"].pop(s_idx)
                        st.rerun()
                    with st.expander("🔀 Reordenar campos", expanded=False):
                        ordenar_campos_por_drag(sec, s_idx, context_key="import")
                    st.markdown("### Campos")
                    for c_idx, campo in enumerate(sec.get("campos", [])):
                        st.text(f"{campo.get('tipo')} - {campo.get('titulo')}")
                        if st.button("Excluir Campo", key=f"imp_del_field_{s_idx}_{c_idx}"):
                            st.session_state.formulario["secoes"][s_idx]["campos"].pop(c_idx)
                            st.rerun()
            st.markdown("---")
            st.subheader("📑 XML atualizado")
            xml_atual = gerar_xml(st.session_state.formulario)
            st.code(xml_atual, language="xml")
            nome_arquivo_imp = st.session_state.formulario.get("nome", "formulario") + ".gfe"
            st.download_button(
                label="Baixar Arquivo",
                data=xml_atual.encode("utf-8"),
                file_name=nome_arquivo_imp,
                mime="application/xml",
                help="O arquivo .gfe é 100% compatível com XML do sistema.",
                key="download_gfe_import"
            )
        else:
            st.info("Importe um XML ou GFE para começar a edição.")
    with colR:
        preview_formulario(st.session_state.formulario, context_key="import")
