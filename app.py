from flask import Flask, render_template_string, request, redirect, url_for
from wtforms import Form, StringField, SelectField, BooleanField, IntegerField, FieldList, FormField
from wtforms.validators import InputRequired

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

<hr>
<h3>Dados Recebidos</h3>
<pre>{{ dados | safe }}</pre>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    form = FormularioForm(request.form)

    if not form.secoes:
        form.secoes.append_entry()

    if request.method == "POST":
        if any(key.startswith("add_secao") for key in request.form.keys()):
            form.secoes.append_entry()
            return render_template_string(template, form=form, dados={}, enumerate=enumerate)

        for key in request.form.keys():
            if key.startswith("add_campo_"):
                idx = int(key.split("_")[-1])
                form.secoes.entries[idx].form.campos.append_entry()
                return render_template_string(template, form=form, dados={}, enumerate=enumerate)

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
            return render_template_string(template, form=form, dados=formulario_dict, enumerate=enumerate)

    return render_template_string(template, form=form, dados={}, enumerate=enumerate)

if __name__ == "__main__":
    app.run(debug=True)
