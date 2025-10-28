# --- XML -> estrutura interna (NOVO) ---
import xml.etree.ElementTree as ET

LIST_TYPES = {"comboBox", "comboFiltro", "grupoRadio", "grupoCheck"}

def _localname(tag: str) -> str:
    # remove namespace {uri}local -> local
    return tag.split('}')[-1] if '}' in tag else tag

def _get_type_attr(el: ET.Element) -> str:
    # pega atributo ...:type (xsi:type, gxsi:type, etc.)
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
    # parágrafo/rotulo
    if tipo in ("paragrafo", "rotulo"):
        return {
            "tipo": tipo,
            "valor": el.attrib.get("valor", el.attrib.get("descricao", el.attrib.get("titulo", ""))),
            "largura": largura,
            "obrigatorio": False,
            "in_tabela": False,
        }
    # listas
    if tipo in LIST_TYPES:
        titulo = el.attrib.get("titulo", "")
        desc = el.attrib.get("descricao", titulo)
        obrig = _to_bool(el.attrib.get("obrigatorio", "false"))
        colunas = int(el.attrib.get("colunas", "1") or 1)
        chave_dom = el.attrib.get("dominio", "")  # chave do bloco <dominios>
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
    # demais campos
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
    # estrutura: elemento[gxsi:type=tabela] > linhas > linha* > celulas > celula* > elementos > elemento*
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
    # filhos: elementos > elemento*
    for child in sec_el:
        if _localname(child.tag) != "elementos":
            continue
        for el in child:
            if _localname(el.tag) != "elemento":
                continue
            tipo_el = _get_type_attr(el)  # "seccao" não esperado aqui; "tabela" ou campos
            if tipo_el == "tabela":
                tabela = _parse_tabela(el, dom_map)
                sec["elementos"].append({"tipo_elemento": "tabela", "tabela": tabela})
            else:
                campo = _parse_campo(el, dom_map)
                sec["elementos"].append({"tipo_elemento": "campo", "campo": campo})
    return sec

def parse_formulario_from_xml(source) -> dict:
    """
    source: path, file-like (UploadedFile) ou bytes compatíveis com ET.parse
    """
    tree = ET.parse(source)  # aceita UploadedFile diretamente
    root = tree.getroot()
    dom_map = _parse_dominios(root)

    nome = root.attrib.get("nome", "")
    versao = root.attrib.get("versao", "1.0")

    secoes = []
    # root > elementos > elemento[gxsi/xsi:type='seccao']*
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
        "dominios": []  # opcional; domínios já injetados por campo via dom_map
    }
