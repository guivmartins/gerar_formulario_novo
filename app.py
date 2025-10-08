# -------------------------
# Aba 2 - Importar, Editar e Expandir XML
# -------------------------
with aba[1]:
    st.header("Importar / Editar XML")

    # Upload
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

    # Editor do formulário importado
    if st.session_state.formulario.get("secoes"):
        st.subheader("Editar Metadados do Formulário")
        col_a, col_b = st.columns([2,1])
        with col_a:
            st.session_state.formulario["nome"] = st.text_input("Nome do Formulário", value=st.session_state.formulario.get("nome",""), key="imp_nome")
        with col_b:
            st.session_state.formulario["versao"] = st.text_input("Versão", value=st.session_state.formulario.get("versao","1.0"), key="imp_versao")

        st.markdown("---")
        st.subheader("Seções")

        # Listagem e edição de seções
        for s_idx, sec in enumerate(st.session_state.formulario["secoes"]):
            with st.expander(f"Seção [{s_idx}] - {sec.get('titulo','(sem título)')}", expanded=False):
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

                if st.button("Excluir Seção", key=f"imp_sec_del_{s_idx}"):
                    st.session_state.formulario["secoes"].pop(s_idx)
                    st.warning("Seção removida.")
                    st.rerun()

                st.markdown("#### Campos")
                for c_idx, campo in enumerate(sec.get("campos", [])):
                    with st.expander(f"{campo.get('tipo','texto')} - {campo.get('titulo','')}", expanded=False):
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
                                st.warning("Campo removido.")
                                st.rerun()

                # Adicionar novo campo nesta seção
                st.markdown("#### ➕ Adicionar novo campo")
                ntipo = st.selectbox("Tipo do Campo", TIPOS_ELEMENTOS, key=f"imp_add_tipo_{s_idx}")
                ntitulo = st.text_input("Título", key=f"imp_add_tit_{s_idx}")
                nobrig = st.checkbox("Obrigatório?", key=f"imp_add_obrig_{s_idx}")
                nintab = st.checkbox("Dentro da tabela?", key=f"imp_add_intab_{s_idx}")
                nlarg = st.number_input("Largura (px)", min_value=50, max_value=1000, value=450, step=10, key=f"imp_add_larg_{s_idx}")
                nalt = None
                ncols = 1
                ndoms = []
                if ntipo == "texto-area":
                    nalt = st.number_input("Altura (px)", min_value=50, max_value=1000, value=100, step=10, key=f"imp_add_alt_{s_idx}")
                if ntipo in ["comboBox","comboFiltro","grupoRadio","grupoCheck"]:
                    ncols = st.number_input("Colunas", min_value=1, max_value=5, value=1, step=1, key=f"imp_add_cols_{s_idx}")
                    nqtd = st.number_input("Qtd. de Itens no Domínio", min_value=1, max_value=50, value=2, key=f"imp_add_qdom_{s_idx}")
                    for i in range(int(nqtd)):
                        d = st.text_input(f"Descrição Item {i+1}", key=f"imp_add_dom_{s_idx}_{i}")
                        if d.strip():
                            ndoms.append({"descricao": d.strip(), "valor": d.strip().upper()})
                if st.button("Adicionar Campo", key=f"imp_add_field_btn_{s_idx}"):
                    st.session_state.formulario["secoes"][s_idx]["campos"].append({
                        "tipo": ntipo,
                        "titulo": ntitulo,
                        "descricao": ntitulo,
                        "obrigatorio": nobrig,
                        "in_tabela": nintab,
                        "largura": nlarg,
                        "altura": nalt,
                        "colunas": ncols,
                        "dominios": ndoms
                    })
                    st.success("Campo adicionado.")
                    st.rerun()

        st.markdown("---")
        # Adicionar nova seção ao importado
        st.subheader("➕ Adicionar nova seção")
        add_sec_tit = st.text_input("Título da nova seção", key="imp_new_sec_tit")
        add_sec_larg = st.number_input("Largura (px)", min_value=100, value=500, step=10, key="imp_new_sec_larg")
        if st.button("Adicionar seção", key="imp_new_sec_btn"):
            st.session_state.formulario["secoes"].append({
                "titulo": add_sec_tit,
                "largura": add_sec_larg,
                "campos": []
            })
            st.success("Seção adicionada.")
            st.rerun()

        st.markdown("---")
        st.subheader("XML atualizado do formulário importado")
        st.code(gerar_xml(st.session_state.formulario), language="xml")
    else:
        st.info("Importe um XML para começar a edição.")
