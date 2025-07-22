                # ADICIONAR AQUI:
                if st.button("🔍 Descobrir Estrutura Yahoo", type="secondary"):
                    if yahoo_email and yahoo_token:
                        salvar_configuracao("yahoo_email", yahoo_email)
                        salvar_configuracao("yahoo_token", yahoo_token)
                        
                        with st.spinner("Descobrindo estrutura do calendário..."):
                            status, resposta = descobrir_estrutura_yahoo()
                            
                        st.info(f"📊 Status: {status}")
                        st.code(resposta, language="xml")
                        
                        if status == 207:
                            st.success("✅ Estrutura descoberta! Procure pelos caminhos <href> acima")
                        else:
                            st.error("❌ Erro ao descobrir estrutura")
                    else:
                        st.warning("⚠️ Preencha email e senha primeiro")
