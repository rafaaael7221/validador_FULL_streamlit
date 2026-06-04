import streamlit as st
import pandas as pd
import io
from main import processar_validacao_completa

st.set_page_config(page_title="Validador CNPJ - Full", layout="centered")
st.title("Validador de CNPJ & comparador de endereços ")
st.markdown("Arraste a planilha abaixo para rodar")

arquivo_enviado = st.file_uploader("Selecione a planilha Excel (.xlsx)", type=["xlsx"])

if arquivo_enviado is not None:
    try:
        df_origem = pd.read_excel(arquivo_enviado)
        st.success(f"Planilha carregada! {len(df_origem)} registros encontrados.")
        
        if st.button("Iniciar Validação Completa"):
            status_texto = st.empty()
            log_container = st.container()
            
            def mostrar_log_completo(pedido, cnpj, tipo_status, detalhe, comparativo=None):
                status_texto.text(f"Processando Pedido: {pedido} | CNPJ: {cnpj}")
                
                with log_container:
                    if tipo_status == "erro_cnpj":
                        st.warning(f"⚠️ Pedido {pedido}: Linha sem CNPJ. Pulando...")
                    elif tipo_status == "erro_api":
                        st.error(f"❌ Pedido {pedido}: Erro na API (Status {detalhe})")
                    elif tipo_status == "erro_geral":
                        st.error(f"❌ Erro crítico no pedido {pedido}: {detalhe}")
                    else:
                        st.markdown(f"### 📦 Pedido: {pedido} | CNPJ: {cnpj}")
                        
                        if tipo_status == "revenda":
                            st.error(f"🚨 CLASSIFICAÇÃO: CANCELAR - CNPJ REVENDA ({detalhe})")
                        elif tipo_status == "divergente":
                            st.warning(f"⚠️ CLASSIFICAÇÃO: ENDEREÇO DIVERGENTE")
                        elif tipo_status == "regular":
                            st.success("✅ CLASSIFICAÇÃO: Pedido Regular")
                            
                        if comparativo:
                            st.text(f"• Planilha: {comparativo['plan']}")
                            st.text(f"• Receita:  {comparativo['rec']}")
                            st.caption(f"📊 Status: {comparativo['detalhes']}")
                        st.markdown("---")

            # Aciona o motor do main.py
            dados_validados = processar_validacao_completa(df_origem, mostrar_log_completo)
            
            status_texto.success("✅ Verificação Concluída!")
            
            if dados_validados:
                df_resultado = pd.DataFrame(dados_validados)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_resultado.to_excel(writer, index=False, sheet_name='Resultado_Completo')
                    
                st.markdown("### Seu resultado está pronto!")
                st.download_button(
                    label="📥 Baixar Planilha de Resultados",
                    data=buffer.getvalue(),
                    file_name="resultado_full.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
