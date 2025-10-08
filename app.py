def preview_formulario(formulario: dict):
    st.header("📋 Pré-visualização do Formulário")
    st.subheader(formulario.get("nome", ""))
    for sec in formulario.get("secoes", []):
        st.markdown(f"### {sec.get('titulo')}")
        tabela_aberta = False
        for campo in sec.get("campos", []):
            tipo = campo.get("tipo")
            key_prev = f"prev_{sec.get('titulo')}_{campo.get('titulo')}"
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
            elif tipo in ["paragrafo", "rotulo"]:
                st.markdown(f"**{campo.get('titulo')}**")

        if tabela_aberta:
            st.markdown("</div>", unsafe_allow_html=True)
