from flask import Flask, render_template_string, request
from wtforms import Form, StringField, SelectField, BooleanField, IntegerField, FieldList, FormField
from wtforms.validators import InputRequired
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = Flask(__name__)
app.secret_key = 'secret'

TIPOS_ELEMENTOS = [
    "texto", "texto-area", "data", "moeda", "cpf", "cnpj", "email",
    "telefone", "check", "comboBox", "comboFiltro", "grupoRadio",
    "grupoCheck", "paragrafo", "rotulo"
]

class CampoForm(Form):
    tipo = SelectField("Tipo do Campo", choices=[(t, t) for t in TIPOS_ELEMENTOS])
    titulo = StringField("Título do Campo", validators=[InputRequired()])
    obrigatorio = BooleanField("Obrigatório")
    in_tabela = BooleanField("Dentro da tabela")
    largura = IntegerField("Largura (px)", default=450)
    altura = IntegerField("Altura (px, só texto-area)", default=100)
    colunas = IntegerField("Colunas (domínios)", default=1)
    dominios = StringField("Domínios (descrição separada por vírgula)")

class SecaoForm(Form):
    titulo = StringField("Título da Seção", validators=[InputRequired()])
    largura = IntegerField("Largura da Seção", default=500)
    campos = FieldList(FormField(CampoForm), min_entries=1)

class FormularioForm(Form):
    nome = StringField("Nome do Formulário", validators=[InputRequired()])
    secoes = FieldList(FormField(SecaoForm), min_entries=1)

template = """
<!doctype html>
<title>Construtor de Formulários Flask</title>
<h2>Construtor de Formulários 6.4 (Flask + WTForms)</h2>
<form method="post">
    <label>{{ form.nome.label }}:</label>
    {{ form.nome(size=60) }}<br><br>

    {% for s_idx, secao in enumerate(form.secoes) %}
      <fieldset style="border:1px solid #ccc; padding:10px; margin-bottom:20px;">
        <legend>Seção {{ s_idx + 1 }}</legend>
        <label>{{ secao.titulo.label }}:</label>
        {{ secao.titulo(size=40) }}<br>
        <label>{{ secao.largura.label }}:</label>
        {{ secao.largura(min=100) }}<br><br>

        {% for c_idx, campo in enumerate(secao.campos) %}
          <div style="border:1px solid #eee; padding:5px; margin-bottom:5px;">
            <b>Campo {{ c_idx + 1 }}</b><br>
            <label>{{ campo.tipo.label }}:</label>
            {{ campo.tipo() }}<br>
            <label>{{ campo.titulo.label }}:</label>
            {{ campo.titulo(size=30) }}<br>
            <label>{{ campo.obrigatorio.label }}:</label>
            {{ campo.obrigatorio() }}<br>
            <label>{{ campo.in_tabela.label }}:</label>
            {{ campo.in_tabela() }}<br>
            <label>{{ campo.largura.label }}:</label>
            {{ campo.largura(min=100) }}<br>
            <label>{{ campo.altura.label }}:</label>
            {{ campo.altura(min=50) }}<br>
            <label>{{ campo.colunas.label }}:</label>
            {{ campo.colunas(min=1, max=5) }}<br>
            <label>{{ campo.dominios.label }}:</label>
            {{ campo.dominios(size=40) }}<br>
          </div>
        {% endfor %}
        <button name="add_campo_{{ s_idx }}" type="submit">➕ Adicionar Campo</button>
      </fieldset>
    {% endfor %}
    <button name="add_secao" type="submit">➕ Adicionar Seção</button>
    <br><br>
    <input type="submit" value="Salvar Formulário">
</form>

{% if dados and dados.secoes %}
<hr>
<h3>Pré-visualização do Formulário</h3>
{% for secao in dados.secoes %}
  <h4>{{ secao.titulo }}</h4>
  {% for campo in secao.campos %}
    <div>
      <label>{{ campo.titulo }} {% if campo.obrigatorio %}*{% endif %}</label>
      {% if campo.tipo == 'texto' %}
        <input type="text" />
      {% elif campo.tipo == 'check' %}
        <input type="checkbox" />
      {% elif campo.tipo in ['comboBox', 'grupoRadio'] %}
        <select>
          {% for dom in campo.dominios %}
            <option>{{ dom.descricao }}</option>
          {% endfor %}
        </select>
      {% else %}
        <input type="text" />
      {% endif %}
    </div>
  {% endfor %}
{% endfor %}
<hr>
<h3>Pré-visualização XML</h3>
<pre>{{ xml | safe }}</pre>
{% endif %}
"""

def gerar_xml(formulario: dict) -> str:
    root = ET.Element("gxsi:formulario", {
        "nome": formulario.get("nome", ""),
        "versao": "1.0",
        "xmlns:gxsi": "http://www.w3.org/2001/XMLSchema-instance"
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

            # parágrafo / rótulo
            if tipo in ["paragrafo", "rotulo"]:
                ET.SubElement(elementos_destino, "elemento", {
                    "gxsi:type": tipo,
                    "valor": campo.get("titulo", titulo),
                    "largura": largura
                })
                continue

            # campos com domínio
            if tipo in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] and campo.get("dominios"):
                chave_dom = titulo.replace(" ", "")[:20].upper()
                attrs = {
                    "gxsi:type": tipo,
                    "titulo": titulo,
                    "descricao": campo.get("titulo", titulo),
                    "obrigatorio": obrig,
                    "largura": largura,
                    "colunas": str(campo.get("colunas", 1)),
                    "dominio": chave_dom
                }
                ET.SubElement(elementos_destino, "elemento", attrs)

                # domínio global
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

            # campos comuns
            attrs = {
                "gxsi:type": tipo,
                "titulo": titulo,
                "descricao": campo.get("titulo", titulo),
                "obrigatorio": obrig,
                "largura": largura
            }
            if tipo == "texto-area" and campo.get("altura"):
                attrs["altura"] = str(campo.get("altura"))
            el = ET.SubElement(elementos_destino, "elemento", attrs)
            ET.SubElement(el, "conteudo", {"gxsi:type": "valor"})

    root.append(dominios_global)
    xml_bytes = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(xml_bytes)
    return reparsed.toprettyxml(indent="  ")

@app.route("/", methods=["GET", "POST"])
def index():
    form = FormularioForm(request.form)

    if not form.secoes:
        form.secoes.append_entry()

    xml_str = ""
    formulario_dict = {}

    if request.method == "POST":
        if any(key.startswith("add_secao") for key in request.form.keys()):
            form.secoes.append_entry()
            return render_template_string(template, form=form, dados={}, xml="", enumerate=enumerate)

        for key in request.form.keys():
            if key.startswith("add_campo_"):
                idx = int(key.split("_")[-1])
                form.secoes.entries[idx].form.campos.append_entry()
                return render_template_string(template, form=form, dados={}, xml="", enumerate=enumerate)

        if form.validate():
            formulario_dict = {
                "nome": form.nome.data,
                "secoes": []
            }

            for secao_form in form.secoes:
                secao = {
                    "titulo": secao_form.titulo.data,
                    "largura": secao_form.largura.data,
                    "campos": []
                }
                for campo_form in secao_form.campos:
                    dominio_lista = [d.strip() for d in campo_form.dominios.data.split(",")] if campo_form.dominios.data else []
                    campo = {
                        "tipo": campo_form.tipo.data,
                        "titulo": campo_form.titulo.data,
                        "obrigatorio": campo_form.obrigatorio.data,
                        "in_tabela": campo_form.in_tabela.data,
                        "largura": campo_form.largura.data,
                        "altura": campo_form.altura.data if campo_form.tipo.data == "texto-area" else None,
                        "colunas": campo_form.colunas.data if campo_form.tipo.data in ["comboBox", "comboFiltro", "grupoRadio", "grupoCheck"] else None,
                        "dominios": [{"descricao": d, "valor": d.upper()} for d in dominio_lista]
                    }
                    secao["campos"].append(campo)
                formulario_dict["secoes"].append(secao)

            xml_str = gerar_xml(formulario_dict)

    return render_template_string(template, form=form, dados=formulario_dict, xml=xml_str, enumerate=enumerate)

if __name__ == "__main__":
    app.run(debug=True)
