# app.py - Construtor de Formulários 6.4 (estável)
# Funcionalidades: Construtor, Importação/edição de XML, Pré-visualização em ambas as abas,
# correção paragrafo/rotulo, e reordenação por arrastar-e-soltar (streamlit-sortables compatível)
# com fallback por botões.

import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
from streamlit_sortables import sort_items  # pip install streamlit-sortables

st.set_page_config(page_title="Construtor de Formulários 6.4", layout="wide")

# -------------------------
# Estado inicial
# -------------------------
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

# -------------------------
# Utilidades XML
# -------------------------
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

        tabela_aberta = None
        elementos_destino = subelems

        for campo in sec.get("campos", []):
            tipo = campo.get("tipo", "texto")
            titulo = campo.get("titulo", "")
            obrig = str(bool(campo.get("obrigatorio", False))).lower()
            largura = str(campo.get("largura", 450))

            if campo.get("in_tabela"):
                if tabela_aberta is None:
                    tabela_aberta = ET.SubElement(subelems, "elemento", {"gxsi:type": "tabela"})
                    linhas_tag = ET.SubElement(tabela_aberta, "linhas")
                    linha_tag = ET.SubElement(linhas_tag, "linha")
                    celulas_tag = ET.SubElement(linha_tag, "celulas")
                    celula_tag = ET.SubElement(celulas_tag, "celula", {"linhas": "1", "colunas": "1"})
                    elementos_destino = ET.SubElement(celula_tag, "elementos")
            else:
                tabela_aberta = None
                elementos_destino = subelems

            if tipo in ["paragrafo", "rotulo"]:
                ET.SubElement(elementos_destino, "elemento", {
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
                ET.SubElement(elementos_destino, "elemento", attrs)

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
            el = ET.SubElement(elementos_destino, "elemento", attrs)
            ET.SubElement(el, "conteudo", {"gxsi:type": "valor"})

    root.append(dominios_global)
    return _prettify_xml(root)

# ---------- Parser de importação ----------
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

# ---------- Pré-visualização compartilhada (keys únicas por aba) ----------
def preview_formulario(formulario: dict, context_key: str = "main"):
    st.header("📋 Pré-visualização do Formulário")
    st.subheader(formulario.get("nome", ""))
    for s_idx, sec in enumerate(formulario.get("secoes", [])):
        st.markdown(f"### {sec.get('titulo')}")
        tabela_aberta = False
        for c_idx, campo in enumerate(sec.get("campos", [])):
            tipo = campo.get("tipo")
            key_prev = f"prev_{context_key}_{s_idx}_{c_idx}_{sec.get('titulo')}_{campo.get('titulo')}"
            if campo.get("in_tabela") and not tabela_aberta:
                st.markdown("<div style='border:1px solid #ccc; padding:5px;'>", unsafe_allow_html=True)
                tabela_aberta = True
            if not campo.get("in_tabela") and tabela_aberta:
                st.markdown("</div>", unsafe_allow_html=True)
                tabela_aberta = False

            if tipo == "texto":
                st.text_input(campo.get("titulo", ""), key=key_prev)
            elif tipo == "texto-area":
                st.text_area(campo.get("titulo", ""), height=campo.get("altura", 100), key=key_prev)
            elif tipo in ["comboBox", "comboFiltro", "grupoCheck"]:
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

        if tabela_aberta:
            st.markdown("</div>", unsafe_allow_html=True)

# ---------- Fallback por botões (subir/descer) ----------
def mover_item(lista, idx, direcao):
    novo = idx + direcao
    if 0 <= novo < len(lista):
        lista[idx], lista[novo] = lista[novo], lista[idx]
        return True
    return False

# ---------- Reordenar por drag-and-drop (streamlit-sortables compat) ----------
def ordenar_campos_por_drag(secao: dict, sec_index: int, context_key: str) -> None:
    campos = secao.get('campos', [])
    if not campos:
        st.info("Nenhum campo para reordenar.")
        return

    # Lista de strings para máxima compatibilidade
    itens = [f"{i} | {campos[i].get('tipo','texto')} - {campos[i].get('titulo','')}" for i in range(len(campos))]

    st.markdown("Arraste para reordenar os campos abaixo (ou use os botões):")
    comp_key = f"sortable_{context_key}_{sec_index}"
    sorted_items = sort_items(
        itens,
        multi_containers=False,
        direction="vertical",
        custom_style={"border": "1px dashed #ddd", "padding": "8px", "borderRadius": "6px"},
        key=comp_key,
    )

    # Se houve reorder, aplica
    if sorted_items and sorted_items != itens:
        nova_ordem_indices = [int(s.split(" | ", 1)[0]) for s in sorted_items]
        secao["campos"] = [campos[i] for i in nova_ordem_indices]
        st.success("Ordem dos campos atualizada.")
        st.rerun()

    # Fallback: botões ↑ ↓
    st.markdown("Ou reordene manualmente:")
    for i, c in enumerate(secao["campos"]):
        colA, colB, colC = st.columns([6,1,1])
        with colA:
            st.caption(f"{i+1}. {c.get('tipo','texto')} - {c.get('titulo','')}")
        with colB:
            if st.button("↑", key=f"up_{context_key}_{sec_index}_{i}"):
                if mover_item(secao["campos"], i, -1):
                    st.rerun()
        with colC:
            if st.button("↓", key=f"down_{context_key}_{sec_index}_{i}"):
                if mover_item(secao["campos"], i, +1):
                    st.rerun()

# -------------------------
# Abas
# -------------------------
aba = st.tabs(["Construtor", "Importar XML"])

# -------------------------
# Aba 1 - Construtor
# -------------------------
with aba[0]:
    col1, col2 = st.columns(2)

    with col1:
        st.title("Construtor de Formulários 6.4")
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

                st.markdown("### Campos")
                for c_idx, campo in enumerate(sec.get("campos", [])):
                    st.text(f"{campo.get('tipo')} - {campo.get('titulo')}")
                    if st.button("Excluir Campo", key=f"del_field_{s_idx}_{c_idx}"):
                        st.session_state.formulario["secoes"][s_idx]["campos"].pop(c_idx)
                        st.rerun()

        if st.session_state.formulario.get("secoes"):
            last_idx = len(st.session_state.formulario["secoes"]) - 1
            secao_atual = st.session_state.formulario["secoes"][last_idx]
            with st.expander(f"➕ Adicionar Campos à seção: {secao_atual.get('titulo','')}", expanded=True):
                tipo = st.selectbox("Tipo do Campo", TIPOS_ELEMENTOS, key=f"type_{last_idx}")
                titulo = st.text_input("Título do Campo", key=f"title_{last_idx}")
                obrig = st.checkbox("Obrigatório", key=f"obrig_{last_idx}")
                in_tabela = st.checkbox("Dentro da tabela?", key=f"tabela_{last_idx}")
                largura = st.number_input("Largura (px)", min_value=100, value=450, step=10, key=f"larg_{last_idx}")

                altura = None
                if tipo == "texto-area":
                    altura = st.number_input("Altura", min_value=50, value=100, step=10, key=f"alt_{last_idx}")

                colunas = 1
                dominios_temp = []
                if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"]:
                    colunas = st.number_input("Colunas", min_value=1, max_value=5, value=1, key=f"colunas_{last_idx}")
                    qtd_dom = st.number_input("Qtd. de Itens no Domínio", min_value=1, max_value=50, value=2, key=f"qtd_dom_{last_idx}")
                    for i in range(int(qtd_dom)):
                        val = st.text_input(f"Descrição Item {i+1}", key=f"desc_{last_idx}_{i}")
                        if val:
                            dominios_temp.append({"descricao": val, "valor": val.upper()})

                if st.button("Adicionar Campo", key=f"add_field_{last_idx}"):
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
                    secao_atual["campos"].append(campo)
                    st.rerun()

    with col2:
        preview_formulario(st.session_state.formulario, context_key="builder")

    st.markdown("---")
    st.subheader("📑 Pré-visualização XML")
    st.code(gerar_xml(st.session_state.formulario), language="xml")

# -------------------------
# Aba 2 - Importar / Editar XML (mesmo layout)
# -------------------------
with aba[1]:
    colL, colR = st.columns(2)

    with colL:
        st.title("Importar / Editar XML")

        up = st.file_uploader("Selecione um arquivo XML", type=["xml"], key="uploader_xml_editor")
        if up and st.button("Carregar XML"):
            try:
                xml_str = up.getvalue().decode("utf-8")
                root = ET.fromstring(xml_str)
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
                                "campos": []
                            }
                            sub = el.find("elementos")
                            sec["campos"] = _buscar_campos_rec(sub, dominios_map)
                            novo["secoes"].append(sec)

                st.session_state.formulario = novo
                st.success("XML carregado e pronto para edição.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar XML: {e}")

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
                        with st.expander(f"Editar: {campo.get('tipo')} - {campo.get('titulo')}", expanded=False):
                            tipo = st.selectbox("Tipo", TIPOS_ELEMENTOS, index=TIPOS_ELEMENTOS.index(campo.get("tipo","texto")), key=f"imp_tipo_{s_idx}_{c_idx}")
                            titulo = st.text_input("Título", value=campo.get("titulo",""), key=f"imp_tit_{s_idx}_{c_idx}")
                            descricao = st.text_input("Descrição", value=campo.get("descricao", campo.get("titulo","")), key=f"imp_desc_{s_idx}_{c_idx}")
                            obrig = st.checkbox("Obrigatório", value=campo.get("obrigatorio",False), key=f"imp_obrig_{s_idx}_{c_idx}")
                            in_tabela = st.checkbox("Dentro da tabela?", value=campo.get("in_tabela",False), key=f"imp_intab_{s_idx}_{c_idx}")
                            largura = st.number_input("Largura (px)", min_value=50, max_value=1000, value=campo.get("largura",450), step=10, key=f"imp_larg_{s_idx}_{c_idx}")

                            altura = campo.get("altura")
                            if tipo == "texto-area":
                                altura = st.number_input("Altura (px)", min_value=50, max_value=1000, value=altura or 100, step=10, key=f"imp_alt_{s_idx}_{c_idx}")
                            else:
                                altura = None

                            colunas = campo.get("colunas",1)
                            dominios = campo.get("dominios",[])
                            if tipo in ["comboBox","comboFiltro","grupoRadio","grupoCheck"]:
                                colunas = st.number_input("Colunas", min_value=1, max_value=5, value=colunas, step=1, key=f"imp_cols_{s_idx}_{c_idx}")
                                qtd_dom = st.number_input("Qtd. de Itens no Domínio", min_value=1, max_value=50, value=len(dominios) or 2, key=f"imp_qdom_{s_idx}_{c_idx}")
                                novos_dom = []
                                for i in range(int(qtd_dom)):
                                    base = dominios[i]["descricao"] if i < len(dominios) else ""
                                    d = st.text_input(f"Descrição Item {i+1}", value=base, key=f"imp_dom_{s_idx}_{c_idx}_{i}")
                                    if d.strip():
                                        novos_dom.append({"descricao": d.strip(), "valor": d.strip().upper()})
                                dominios = novos_dom
                            else:
                                colunas = 1
                                dominios = []

                            c_left, c_mid, c_right = st.columns([1,1,1])
                            with c_left:
                                if st.button("Salvar Campo", key=f"imp_save_field_{s_idx}_{c_idx}"):
                                    st.session_state.formulario["secoes"][s_idx]["campos"][c_idx] = {
                                        "tipo": tipo,
                                        "titulo": titulo,
                                        "descricao": descricao,
                                        "obrigatorio": obrig,
                                        "in_tabela": in_tabela,
                                        "largura": largura,
                                        "altura": altura,
                                        "colunas": colunas,
                                        "dominios": dominios
                                    }
                                    st.success("Campo salvo.")
                            with c_mid:
                                if st.button("Excluir Campo", key=f"imp_del_field_{s_idx}_{c_idx}"):
                                    st.session_state.formulario["secoes"][s_idx]["campos"].pop(c_idx)
                                    st.rerun()

            st.markdown("---")
            st.subheader("📑 XML atualizado")
            st.code(gerar_xml(st.session_state.formulario), language="xml")
        else:
            st.info("Importe um XML para começar a edição.")

    with colR:
        preview_formulario(st.session_state.formulario, context_key="import")
