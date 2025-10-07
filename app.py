import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
from io import StringIO

from streamlit import experimental_rerun  # Importa explicitamente

st.set_page_config(page_title="Construtor de Formulários 6.4 + Edição + Importação XML", layout="wide")

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

    ns = {'gxsi': "http://www.w3.org/2001/XMLSchema-instance"}

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
                        campo = {
                            "tipo": tipo,
                            "titulo": campo_el.attrib.get("titulo", ""),
                            "descricao": campo_el.attrib.get("descricao", campo_el.attrib.get("titulo", "")),
                            "obrigatorio": campo_el.attrib.get("obrigatorio", "false").lower() == "true",
                            "largura": int(campo_el.attrib.get("largura", 450)),
                            "altura": int(campo_el.attrib.get("altura", 100)) if tipo == "texto-area" and "altura" in campo_el.attrib else None,
                            "colunas": int(campo_el.attrib.get("colunas", 1)) if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] else None,
                            "in_tabela": False,
                            "dominios": []
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
    dominios_global = ET.Element("dominios")

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

            el = ET.SubElement(subelems, "elemento", attrs)
            ET.SubElement(el, "conteudo", {"gxsi:type": "valor"})

    root.append(dominios_global)
    return _prettify_xml(root)

# Inicializa estado da aplicação
if "formulario" not in st.session_state:
    st.session_state.formulario = {
        "nome": "",
        "versao": "1.0",
        "secoes": [],
        "dominios": []
    }
if "editando_secao" not in st.session_state:
    st.session_state.editando_secao = None
if "editando_campo" not in st.session_state:
    st.session_state.editando_campo = None

st.title("Construtor de Formulários 6.4 - Edição e Importação XML")

# Importar XML
with st.sidebar.expander("Importar Formulário XML"):
    uploaded_file = st.file_uploader("Escolha o arquivo XML", type=["xml"])
    if uploaded_file:
        content = uploaded_file.getvalue().decode("utf-8")
        try:
            formulario_parseado = xml_to_dict(content)
            st.session_state.formulario = formulario_parseado
            st.success("XML importado com sucesso!")
            experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao importar XML: {e}")

# Edição nome formulário
st.session_state.formulario["nome"] = st.text_input("Nome do Formulário", st.session_state.formulario["nome"])

# Adicionar nova seção
with st.expander("Adicionar Nova Seção", expanded=False):
    nova_secao_titulo = st.text_input("Título Nova Seção", key="nova_secao_titulo")
    nova_secao_largura = st.number_input("Largura Nova Seção", min_value=100, value=500, step=10, key="nova_secao_largura")
    if st.button("Adicionar Seção"):
        if nova_secao_titulo.strip():
            st.session_state.formulario["secoes"].append({
                "titulo": nova_secao_titulo,
                "largura": nova_secao_largura,
                "campos": []
            })
            experimental_rerun()
        else:
            st.warning("Informe o título da seção para adicionar.")

# Listagem e edição das seções e campos
for s_idx, secao in enumerate(st.session_state.formulario.get("secoes", [])):
    with st.expander(f"Seção [{s_idx}] - {secao['titulo']}", expanded=st.session_state.editando_secao == s_idx):
        if st.button("Editar Seção", key=f"editar_secao_{s_idx}"):
            st.session_state.editando_secao = s_idx
            st.session_state.editando_campo = None
            experimental_rerun()

        if st.session_state.editando_secao == s_idx:
            novo_titulo = st.text_input("Título da Seção", value=secao["titulo"], key=f"edit_titulo_secao_{s_idx}")
            nova_largura = st.number_input("Largura da Seção", min_value=100, value=secao.get("largura", 500), key=f"edit_largura_secao_{s_idx}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvar Seção", key=f"salvar_secao_{s_idx}"):
                    st.session_state.formulario["secoes"][s_idx]["titulo"] = novo_titulo
                    st.session_state.formulario["secoes"][s_idx]["largura"] = nova_largura
                    st.session_state.editando_secao = None
                    experimental_rerun()
            with col2:
                if st.button("Cancelar", key=f"cancelar_secao_{s_idx}"):
                    st.session_state.editando_secao = None
                    experimental_rerun()

        st.markdown("### Campos:")
        for c_idx, campo in enumerate(secao.get("campos", [])):
            col1, col2, col3 = st.columns([8, 1, 1])
            with col1:
                st.text(f"{campo.get('tipo', 'texto')} - {campo.get('titulo', '')}")
            with col2:
                if st.button("Editar", key=f"editar_campo_{s_idx}_{c_idx}"):
                    st.session_state.editando_secao = s_idx
                    st.session_state.editando_campo = (s_idx, c_idx)
                    experimental_rerun()
            with col3:
                if st.button("Excluir", key=f"excluir_campo_{s_idx}_{c_idx}"):
                    st.session_state.formulario["secoes"][s_idx]["campos"].pop(c_idx)
                    experimental_rerun()

        # Edição de campo ativo
        if st.session_state.editando_campo and st.session_state.editando_campo[0] == s_idx:
            c_idx = st.session_state.editando_campo[1]
            campo = secao["campos"][c_idx]

            tipo = st.selectbox("Tipo", TIPOS_ELEMENTOS, index=TIPOS_ELEMENTOS.index(campo.get("tipo", "texto")), key=f"edit_tipo_{s_idx}_{c_idx}")
            titulo = st.text_input("Título", value=campo.get("titulo", ""), key=f"edit_titulo_{s_idx}_{c_idx}")
            descricao = st.text_input("Descrição", value=campo.get("descricao", titulo), key=f"edit_desc_{s_idx}_{c_idx}")
            obrig = st.checkbox("Obrigatório", value=campo.get("obrigatorio", False), key=f"edit_obrig_{s_idx}_{c_idx}")
            in_tabela = st.checkbox("Dentro da Tabela", value=campo.get("in_tabela", False), key=f"edit_intabela_{s_idx}_{c_idx}")
            largura = st.number_input("Largura", min_value=100, value=campo.get("largura", 450), key=f"edit_largura_{s_idx}_{c_idx}")
            altura = st.number_input("Altura (texto-area)", min_value=50, value=campo.get("altura") or 100, key=f"edit_altura_{s_idx}_{c_idx}") if tipo == "texto-area" else None
            colunas = st.number_input("Colunas (domínios)", min_value=1, max_value=10, value=campo.get("colunas", 1), key=f"edit_colunas_{s_idx}_{c_idx}") if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] else None

            dominios = campo.get("dominios", [])
            dominios_text = ", ".join([d["descricao"] for d in dominios])
            dominios_text = st.text_area("Domínios (descrições separadas por vírgula)", value=dominios_text, key=f"edit_dominios_{s_idx}_{c_idx}")
            dominios_list = [{"descricao": d.strip(), "valor": d.strip().upper()} for d in dominios_text.split(",") if d.strip()]

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvar Campo", key=f"salvar_campo_{s_idx}_{c_idx}"):
                    st.session_state.formulario["secoes"][s_idx]["campos"][c_idx].update({
                        "tipo": tipo,
                        "titulo": titulo,
                        "descricao": descricao,
                        "obrigatorio": obrig,
                        "in_tabela": in_tabela,
                        "largura": largura,
                        "altura": altura,
                        "colunas": colunas,
                        "dominios": dominios_list
                    })
                    st.session_state.editando_campo = None
                    experimental_rerun()
            with col2:
                if st.button("Cancelar Edição", key=f"cancelar_campo_{s_idx}_{c_idx}"):
                    st.session_state.editando_campo = None
                    experimental_rerun()

# Adicionar campo na última seção
if st.session_state.formulario.get("secoes"):
    last_idx = len(st.session_state.formulario["secoes"]) - 1
    secao_atual = st.session_state.formulario["secoes"][last_idx]
    with st.expander(f"➕ Adicionar Campo à Seção: {secao_atual['titulo']}", expanded=False):
        tipo = st.selectbox("Tipo do Campo", TIPOS_ELEMENTOS, key="add_tipo_campo")
        titulo = st.text_input("Título do Campo", key="add_titulo_campo")
        obrig = st.checkbox("Obrigatório?", key="add_obrigatorio_campo")
        in_tabela = st.checkbox("Dentro da Tabela?", key="add_in_tabela_campo")
        largura = st.number_input("Largura (px)", min_value=100, value=450, step=10, key="add_largura_campo")
        altura = None
        if tipo == "texto-area":
            altura = st.number_input("Altura (px)", min_value=50, value=100, step=10, key="add_altura_campo")
        colunas = 1
        dominios = []
        if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"]:
            colunas = st.number_input("Colunas", min_value=1, max_value=5, value=1, key="add_colunas_campo")
            dominios_text = st.text_area("Domínios (descrições separadas por vírgula)", key="add_dominios_campo")
            dominios = [{"descricao": d.strip(), "valor": d.strip().upper()} for d in dominios_text.split(",") if d.strip()]

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
            experimental_rerun()

st.markdown("---")
st.subheader("📑 Pré-visualização XML")
st.code(gerar_xml(st.session_state.formulario), language="xml")
