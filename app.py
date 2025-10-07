import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom

st.set_page_config(page_title="Construtor Formulários 6.4 Corrigido", layout="wide")

TIPOS_ELEMENTOS = [
    "texto", "texto-area", "data", "moeda", "cpf", "cnpj", "email",
    "telefone", "check", "comboBox", "comboFiltro", "grupoRadio",
    "grupoCheck", "paragrafo", "rotulo"
]

def xml_to_dict(xml_string):
    root = ET.fromstring(xml_string)
    formulario = {
        "nome": root.attrib.get("nome", ""),
        "versao": root.attrib.get("versao", "1.0"),
        "secoes": [],
        "dominios": []
    }

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
            dominios_map[chave] = itens

    elementos = root.find("elementos")
    if elementos is not None:
        for el in elementos.findall("elemento"):
            if el.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "seccao":
                secao = {
                    "titulo": el.attrib.get("titulo", ""),
                    "largura": int(el.attrib.get("largura", 500)),
                    "campos": []
                }
                subelementos = el.find("elementos")
                if subelementos is not None:
                    for campo_el in subelementos.findall("elemento"):
                        tipo = campo_el.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "texto")
                        dominio_chave = campo_el.attrib.get("dominio")
                        dominios_campo = dominios_map.get(dominio_chave, []) if dominio_chave else []
                        campo = {
                            "tipo": tipo,
                            "titulo": campo_el.attrib.get("titulo", ""),
                            "descricao": campo_el.attrib.get("descricao", campo_el.attrib.get("titulo", "")),
                            "obrigatorio": campo_el.attrib.get("obrigatorio", "false").lower() == "true",
                            "largura": int(campo_el.attrib.get("largura", 450)),
                            "altura": int(campo_el.attrib.get("altura", 100)) if tipo == "texto-area" and "altura" in campo_el.attrib else None,
                            "colunas": int(campo_el.attrib.get("colunas", 1)) if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] else None,
                            "in_tabela": False,
                            "dominios": dominios_campo,
                        }
                        secao["campos"].append(campo)
                formulario["secoes"].append(secao)
    return formulario

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
    dominios_global = ET.SubElement(root, "dominios")

    for sec in formulario.get("secoes", []):
        sec_el = ET.SubElement(elementos, "elemento", {
            "gxsi:type": "seccao",
            "titulo": sec.get("titulo", ""),
            "largura": str(sec.get("largura", 500))
        })
        subelems = ET.SubElement(sec_el, "elementos")

        for campo in sec.get("campos", []):
            tipo = campo.get("tipo", "texto")
            titulo = campo.get("titulo", "")
            obrig = str(bool(campo.get("obrigatorio", False))).lower()
            largura = str(campo.get("largura", 450))

            attrs = {
                "gxsi:type": tipo,
                "titulo": titulo,
                "descricao": campo.get("descricao", titulo),
                "obrigatorio": obrig,
                "largura": largura
            }

            if tipo == "texto-area" and campo.get("altura") is not None:
                attrs["altura"] = str(campo.get("altura"))

            if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] and campo.get("dominios"):
                chave_dom = titulo.replace(" ", "")[:20].upper()
                attrs["colunas"] = str(campo.get("colunas", 1))
                attrs["dominio"] = chave_dom

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

            ET.SubElement(subelems, "elemento", attrs)
            ET.SubElement(subelems[-1], "conteudo", {"gxsi:type": "valor"})

    return _prettify_xml(root)

if "formulario" not in st.session_state:
    st.session_state.formulario = {
        "nome": "",
        "versao": "1.0",
        "secoes": []
    }
if "editando_secao" not in st.session_state:
    st.session_state.editando_secao = None
if "editando_campo" not in st.session_state:
    st.session_state.editando_campo = None

st.title("Construtor de Formulários 6.4 - Domínio com campos individuais")

# Importação XML
with st.sidebar.expander("Importar Formulário XML"):
    uploaded_file = st.file_uploader("Selecionar arquivo XML", type=["xml"])
    if uploaded_file:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.formulario = xml_to_dict(content)
            st.success("XML importado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro na importação do XML: {e}")

# Nome do formulário
st.session_state.formulario["nome"] = st.text_input("Nome do Formulário", st.session_state.formulario["nome"])

# Adicionar seção
with st.expander("Adicionar Nova Seção", expanded=False):
    nova_titulo_sec = st.text_input("Título da Seção", key="nova_secao_titulo")
    nova_largura_sec = st.number_input("Largura da Seção (px)", min_value=100, value=500, step=10, key="nova_secao_largura")
    if st.button("Adicionar Seção"):
        if nova_titulo_sec.strip():
            st.session_state.formulario["secoes"].append({
                "titulo": nova_titulo_sec,
                "largura": nova_largura_sec,
                "campos": []
            })
            st.rerun()
        else:
            st.warning("Informe o título da seção.")

for s_idx, secao in enumerate(st.session_state.formulario.get("secoes", [])):
    with st.expander(f"Seção [{s_idx}] - {secao['titulo']}", expanded=st.session_state.editando_secao == s_idx):
        if st.button("Editar Seção", key=f"editar_sec_{s_idx}"):
            st.session_state.editando_secao = s_idx
            st.session_state.editando_campo = None
            st.rerun()

        if st.session_state.editando_secao == s_idx:
            novo_titulo = st.text_input("Título da Seção", value=secao["titulo"], key=f"edit_titulo_sec_{s_idx}")
            nova_largura = st.number_input("Largura (px)", min_value=100, value=secao.get("largura", 500), key=f"edit_largura_sec_{s_idx}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvar Seção", key=f"salvar_sec_{s_idx}"):
                    st.session_state.formulario["secoes"][s_idx].update({
                        "titulo": novo_titulo,
                        "largura": nova_largura
                    })
                    st.session_state.editando_secao = None
                    st.rerun()
            with col2:
                if st.button("Cancelar", key=f"cancelar_sec_{s_idx}"):
                    st.session_state.editando_secao = None
                    st.rerun()

        st.write("Campos:")
        for c_idx, campo in enumerate(secao.get("campos", [])):
            col1, col2, col3 = st.columns([8, 1, 1])
            with col1:
                st.text(f"{campo.get('tipo', 'texto')} - {campo.get('titulo', '')}")
            with col2:
                if st.button("Editar", key=f"edit_campo_{s_idx}_{c_idx}"):
                    st.session_state.editando_secao = s_idx
                    st.session_state.editando_campo = (s_idx, c_idx)
                    st.rerun()
            with col3:
                if st.button("Excluir", key=f"excluir_campo_{s_idx}_{c_idx}"):
                    st.session_state.formulario["secoes"][s_idx]["campos"].pop(c_idx)
                    st.rerun()

        # Edição de campo (modelo campos separados)
        if st.session_state.editando_campo and st.session_state.editando_campo[0] == s_idx:
            c_idx = st.session_state.editando_campo[1]
            campo = secao["campos"][c_idx]

            tipo = st.selectbox("Tipo", TIPOS_ELEMENTOS, index=TIPOS_ELEMENTOS.index(campo.get("tipo", "texto")), key=f"edit_tipo_{s_idx}_{c_idx}")
            titulo = st.text_input("Título", value=campo.get("titulo", ""), key=f"edit_titulo_{s_idx}_{c_idx}")
            descricao = st.text_input("Descrição", value=campo.get("descricao", titulo), key=f"edit_desc_{s_idx}_{c_idx}")
            obrig = st.checkbox("Obrigatório", value=campo.get("obrigatorio", False), key=f"edit_obrig_{s_idx}_{c_idx}")
            in_tabela = st.checkbox("Dentro da Tabela", value=campo.get("in_tabela", False), key=f"edit_intabela_{s_idx}_{c_idx}")

            largura = 450
            altura = None
            colunas = 1
            dominios_list = campo.get("dominios", [])

            if tipo in ["texto", "cpf", "cnpj", "email", "telefone", "moeda", "data", "check", "paragrafo", "rotulo"]:
                largura = st.number_input("Largura (px)", min_value=50, max_value=1000, value=campo.get("largura", 450), key=f"edit_largura_{s_idx}_{c_idx}")
            elif tipo == "texto-area":
                largura = st.number_input("Largura (px)", min_value=50, max_value=1000, value=campo.get("largura", 450), key=f"edit_largura_{s_idx}_{c_idx}")
                altura = st.number_input("Altura (px)", min_value=50, max_value=1000, value=campo.get("altura", 100) or 100, key=f"edit_altura_{s_idx}_{c_idx}")
            elif tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"]:
                colunas = st.number_input("Colunas", min_value=1, max_value=5, value=campo.get("colunas", 1), key=f"edit_colunas_{s_idx}_{c_idx}")
                qtd_dom = st.number_input("Qtd. de Itens no Domínio", min_value=1, max_value=50, value=len(dominios_list) if dominios_list else 2, key=f"edit_qtd_dom_{s_idx}_{c_idx}")
                dom_descricoes = []
                for i in range(int(qtd_dom)):
                    valor_base = dominios_list[i]["descricao"] if i < len(dominios_list) else ""
                    desc = st.text_input(f"Descrição Item {i+1}", value=valor_base, key=f"edit_dom_{s_idx}_{c_idx}_{i}")
                    dom_descricoes.append(desc)
                dominios_list = [{"descricao": d, "valor": d.upper()} for d in dom_descricoes if d.strip()]
            else:
                largura = st.number_input("Largura (px)", min_value=50, max_value=1000, value=campo.get("largura", 450), key=f"edit_largura_{s_idx}_{c_idx}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvar Campo", key=f"salvar_campo_{s_idx}_{c_idx}"):
                    atts = {
                        "tipo": tipo,
                        "titulo": titulo,
                        "descricao": descricao,
                        "obrigatorio": obrig,
                        "in_tabela": in_tabela,
                        "largura": largura,
                        "altura": altura,
                        "colunas": colunas,
                        "dominios": dominios_list
                    }
                    atts = {k: v for k, v in atts.items() if v is not None}
                    st.session_state.formulario["secoes"][s_idx]["campos"][c_idx].update(atts)
                    st.session_state.editando_campo = None
                    st.rerun()
            with col2:
                if st.button("Cancelar Edição", key=f"cancelar_campo_{s_idx}_{c_idx}"):
                    st.session_state.editando_campo = None
                    st.rerun()

if st.session_state.formulario.get("secoes"):
    last_idx = len(st.session_state.formulario["secoes"]) - 1
    secao_atual = st.session_state.formulario["secoes"][last_idx]
    with st.expander(f"➕ Adicionar Campo - Seção: {secao_atual['titulo']}", expanded=False):
        tipo = st.selectbox("Tipo do Campo", TIPOS_ELEMENTOS, key="add_tipo_campo")
        titulo = st.text_input("Título do Campo", key="add_titulo_campo")
        obrig = st.checkbox("Obrigatório?", key="add_obrigatorio_campo")
        in_tabela = st.checkbox("Dentro da Tabela?", key="add_in_tabela_campo")
        largura = st.number_input("Largura (px)", min_value=50, max_value=1000, value=450, step=10, key="add_largura_campo")
        altura = None
        colunas = 1
        dominios = []

        if tipo == "texto-area":
            altura = st.number_input("Altura (px)", min_value=50, max_value=1000, value=100, step=10, key="add_altura_campo")
        if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"]:
            colunas = st.number_input("Colunas", min_value=1, max_value=5, value=1, key="add_colunas_campo")
            qtd_dom = st.number_input("Qtd. de Itens no Domínio", min_value=1, max_value=50, value=2, key="add_qtd_dom_campo")
            dom_descricoes = []
            for i in range(int(qtd_dom)):
                desc = st.text_input(f"Descrição Item {i+1}", key=f"add_dom_{i}_campo")
                dom_descricoes.append(desc)
            dominios = [{"descricao": d, "valor": d.upper()} for d in dom_descricoes if d.strip()]

        if st.button("Adicionar Campo"):
            campo = {
                "tipo": tipo,
                "titulo": titulo,
                "descricao": titulo,
                "obrigatorio": obrig,
                "in_tabela": in_tabela,
                "largura": largura,
                "altura": altura,
                "colunas": colunas,
                "dominios": dominios
            }
            secao_atual["campos"].append(campo)
            st.rerun()

st.markdown("---")
st.subheader("Pré-visualização simples do formulário")
for sec in st.session_state.formulario.get("secoes", []):
    st.markdown(f"### Seção: {sec['titulo']}")
    for campo in sec.get("campos", []):
        st.markdown(f"- **{campo['titulo']}** ({campo['tipo']}) {'*Obrigatório*' if campo.get('obrigatorio') else ''}")

st.markdown("---")
st.subheader("Pré-visualização XML gerado")
st.code(gerar_xml(st.session_state.formulario), language="xml")
