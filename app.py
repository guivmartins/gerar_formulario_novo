import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import xmltodict

st.set_page_config(page_title="Construtor de Formulários Debug Import 8.4", layout="wide")

# ... (mantém o código anterior, omitido aqui para brevidade)

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

                # Exibir para debug antes de sobrescrever
                st.subheader("Conteúdo importado")
                st.write(formulario_dict)

                st.session_state.formulario = formulario_dict
                st.success("Arquivo importado com sucesso!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar arquivo: {str(e)}")
