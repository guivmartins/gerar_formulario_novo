import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom

st.set_page_config(page_title="Construtor de Formulários 7.4", layout="wide")

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
            if campo.get("in_tabela", False): continue
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

def adicionar_campo_secao(secao, campo, finalizar_linha=False, finalizar_tabela=False):
    if campo.get("in_tabela"):
        if not secao.get("tabela_aberta", False):
            secao["tabelas"] = secao.get("tabelas", [])
            secao["tabela_atual"] = []
            secao["tabela_aberta"] = True
            secao["linha_aberta"] = True
            # colunas por linha definidas ou default 2
            if "colunas_por_linha_atual" not in secao:
                secao["colunas_por_linha_atual"] = 2
            secao["tabela_atual"].append([])
        colunas_por_linha = secao.get("colunas_por_linha_atual", 2)
        if secao["linha_aberta"]:
            linha_atual = secao["tabela_atual"][-1]
            while len(linha_atual) < colunas_por_linha:
                linha_atual.append([])
            for idx in range(colunas_por_linha):
                if len(linha_atual[idx]) < 1:
                    linha_atual[idx].append(campo)
                    break
            else:
                st.warning("Linha cheia, finalize para adicionar novo campo.")
        else:
            secao["linha_aberta"] = True
            secao["tabela_atual"].append([[campo]])
        if finalizar_linha:
            secao["linha_aberta"] = False
        if finalizar_tabela:
            secao["tabelas"].append(secao["tabela_atual"])
            secao["tabela_atual"] = []
            secao["tabela_aberta"] = False
            secao["linha_aberta"] = False
            secao.pop("colunas_por_linha_atual", None)
    else:
        if secao.get("tabela_aberta", False):
            if secao.get("linha_aberta", False):
                secao["linha_aberta"] = False
            secao["tabelas"].append(secao["tabela_atual"])
            secao["tabela_atual"] = []
            secao["tabela_aberta"] = False
            secao.pop("colunas_por_linha_atual", None)
        secao.setdefault("campos", []).append(campo)

# Interface aba construtor
aba = st.tabs(["Construtor", "Importar arquivo"])

with aba[0]:
    col1, col2 = st.columns(2)
    with col1:
        st.title("Construtor de Formulários 7.4")
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
                st.markdown("### Campos e Tabelas")
                for c_idx, campo in enumerate(sec.get("campos", [])):
                    st.text(f"{campo.get('tipo')} - {campo.get('titulo')}")
                    if st.button("Excluir Campo", key=f"del_field_{s_idx}_{c_idx}"):
                        st.session_state.formulario["secoes"][s_idx]["campos"].pop(c_idx)
                        st.rerun()
                if "tabelas" in sec:
                    for t_idx, tabela in enumerate(sec["tabelas"]):
                        st.markdown(f"**Tabela {t_idx+1}:**")
                        for l_idx, linha in enumerate(tabela):
                            cel_texts = []
                            for c_idx, celula in enumerate(linha):
                                titulos = ", ".join([c.get("titulo", "") for c in celula])
                                cel_texts.append(f"Celula {c_idx+1}: {titulos}")
                            st.text(f"Linha {l_idx+1}: " + " | ".join(cel_texts))
        if st.session_state.formulario.get("secoes"):
            secao_opcoes = [sec.get("titulo", f"Seção {i}") for i, sec in enumerate(st.session_state.formulario["secoes"])]
            indice_selecao = st.selectbox("Selecione a Seção para adicionar um campo", options=range(len(secao_opcoes)), format_func=lambda i: secao_opcoes[i])
            secao_atual = st.session_state.formulario["secoes"][indice_selecao]

            with st.expander(f"➕ Adicionar Campos à seção: {secao_atual.get('titulo','')}", expanded=True):
                tipo = st.selectbox("Tipo do Campo", TIPOS_ELEMENTOS, key=f"type_add_{indice_selecao}")
                titulo = st.text_input("Título do Campo", key=f"title_add_{indice_selecao}")
                obrig = st.checkbox("Obrigatório", key=f"obrig_add_{indice_selecao}")
                in_tabela = st.checkbox("Dentro da tabela?", key=f"tabela_add_{indice_selecao}")
                finalizar_linha = st.checkbox("Finalizar Linha", key=f"linha_add_{indice_selecao}")
                finalizar_tabela = st.checkbox("Finaliza Tabela", key=f"tab_add_{indice_selecao}")
                largura = st.number_input("Largura (px)", min_value=100, value=450, step=10, key=f"larg_add_{indice_selecao}")
                colunas_por_linha = 2
                if in_tabela and not secao_atual.get("tabela_aberta", False):
                    colunas_por_linha = st.number_input(
                        "Nº de células por linha",
                        min_value=1, max_value=10, value=2,
                        key=f"colunas_linha_{indice_selecao}"
                    )
                elif secao_atual.get("tabela_aberta", False):
                    colunas_por_linha = secao_atual.get("colunas_por_linha_atual", 2)

                secao_atual["colunas_por_linha_atual"] = colunas_por_linha

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
                    adicionar_campo_secao(secao_atual, campo, finalizar_linha, finalizar_tabela)
                    st.rerun()
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

# Aba de importação permanece igual
