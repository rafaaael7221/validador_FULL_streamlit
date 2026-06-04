import time
import pandas as pd
import requests
import streamlit as st
import io

CNAES_REVENDA = [
    "4520001", "4520006", "4520007", "4530701", "4530702", 
    "4530703", "4530704", "4530705", "4530706", "4541202", 
    "4541206", "4541207", "4542101"
]

def limpar_texto(texto):
    if pd.isna(texto) or not texto:
        return ""
    return str(texto).strip().upper()

def limpar_numeros(texto):
    if pd.isna(texto) or not texto:
        return ""
    return "".join(filter(str.isdigit, str(texto)))

# --- TELA INTERFACE STREAMLIT (V7) ---
st.set_page_config(page_title="Validador CNPJ - V7", layout="centered")
st.title("Validador de CNPJ - Apenas Revenda (V7)")
st.markdown("Arraste sua planilha abaixo para verificar os CNAEs e visualizar os endereços oficiais.")

arquivo_enviado = st.file_uploader("Selecione a planilha Excel (.xlsx)", type=["xlsx"])

if arquivo_enviado is not None:
    try:
        df_origem = pd.read_excel(arquivo_enviado)
        st.success(f"Planilha carregada! {len(df_origem)} registros encontrados.")
        
        if st.button("Iniciar Validação"):
            novas_linhas = []
            
            progresso = st.progress(0)
            status_texto = st.empty()
            log_container = st.container()
            
            for index, linha in df_origem.iterrows():
                progresso.progress((index + 1) / len(df_origem))
                
                pedido = linha.get('Pedido', 'N/A')
                cnpj_planilha = limpar_numeros(linha.get('CNPJ', ''))
                
                status_texto.text(f"Processando Pedido: {pedido} | CNPJ: {cnpj_planilha}")
                
                if not cnpj_planilha:
                    continue
                    
                url_api = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_planilha}"
                
                try:
                    resposta = requests.get(url_api)
                    time.sleep(1) # Rate Limit
                    
                    if resposta.status_code != 200:
                        with log_container:
                            st.error(f"❌ Pedido {pedido}: Falha na API (Status {resposta.status_code})")
                        continue
                        
                    dados_receita = resposta.json()
                    
                    # Validação de revenda
                    cnae_principal = limpar_numeros(dados_receita.get('cnae_fiscal', ''))
                    cnaes_empresa = [cnae_principal]
                    for cnae_sec in dados_receita.get('cnaes_secundarios', []):
                        cnaes_empresa.append(limpar_numeros(cnae_sec.get('codigo', '')))
                    
                    cnae_revenda_identificado = next((c for c in cnaes_empresa if c in CNAES_REVENDA), None)
                    
                    # Captura do endereço da Receita
                    tipo_via = limpar_texto(dados_receita.get('tipo_logradouro', ''))
                    nome_via = limpar_texto(dados_receita.get('logradouro', ''))
                    logradouro_rec = f"{tipo_via} {nome_via}".strip() if tipo_via and tipo_via not in nome_via else nome_via
                    
                    numero_rec = limpar_texto(dados_receita.get('numero', ''))
                    complemento_rec = limpar_texto(dados_receita.get('complemento', ''))
                    cidade_rec = limpar_texto(dados_receita.get('municipio', ''))
                    estado_rec = limpar_texto(dados_receita.get('uf', ''))
                    cep_rec = limpar_numeros(dados_receita.get('cep', ''))
                    
                    acao_back, pendencia, resolucao = "", "", ""
                    
                    with log_container:
                        st.markdown(f"### 📦 Pedido: {pedido} | CNPJ: {cnpj_planilha}")
                        if cnae_revenda_identificado:
                            st.error(f"🚨 CLASSIFICAÇÃO: CNPJ REVENDA ({cnae_revenda_identificado})")
                            acao_back = "Cancelar Pedido - CNPJ revenda"
                            pendencia = "CNPJ Revenda"
                            resolucao = "Abrir ticket em massa"
                        else:
                            st.success("📋 CLASSIFICAÇÃO: CNPJ Comum (Não é revenda)")
                        
                        st.text(f"• Logradouro:  '{logradouro_rec}'")
                        st.text(f"• Número:      '{numero_rec}'" + (f" | Complemento: '{complemento_rec}'" if complemento_rec else ""))
                        st.text(f"• Cidade/UF:   '{cidade_rec}/{estado_rec}'")
                        st.text(f"• CEP:         '{cep_rec}'")
                        st.markdown("---")

                    novas_linhas.append({
                        "Pedido": pedido, 
                        "CNPJ": cnpj_planilha, 
                        "Ação Back": acao_back,
                        "Pendência": pendencia, 
                        "Resolução": resolucao
                    })
                    
                except Exception as e_api:
                    with log_container: st.error(f"❌ Erro no pedido {pedido}: {e_api}")
            
            status_texto.success("✅ Processamento da Versão 7 Concluído!")
            
            if novas_linhas:
                df_resultado = pd.DataFrame(novas_linhas)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_resultado.to_excel(writer, index=False, sheet_name='Resultado')
                
                st.download_button(
                    label="📥 Baixar Planilha de Resultados (V7)",
                    data=buffer.getvalue(),
                    file_name="resultado_v7.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
