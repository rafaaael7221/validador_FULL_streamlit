import time
import pandas as pd
import requests

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

def extrair_nucleo_logradouro(texto):
    """Remove prefixos comuns para comparar apenas o nome essencial da rua"""
    t = limpar_texto(texto)
    prefixos = ["RUA ", "R ", "R. ", "AVENIDA ", "AV ", "AV. ", "RODOVIA ", "ROD ", "ALAMEDA ", "AL "]
    for pref in prefixos:
        if t.startswith(pref):
            return t[len(pref):].strip()
    return t

def processar_validacao_completa(df_origem, log_callback):
    """
    Processa a planilha realizando validação de CNAE e cruzamento de endereços.
    """
    novas_linhas = []
    
    for index, linha in df_origem.iterrows():
        pedido = linha.get('Pedido', 'N/A')
        cnpj_planilha = limpar_numeros(linha.get('CNPJ', ''))
        
        if not cnpj_planilha:
            log_callback(pedido, cnpj_planilha, "erro_cnpj", None)
            continue
            
        url_api = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_planilha}"
        
        try:
            resposta = requests.get(url_api)
            time.sleep(3) # Rate Limit
            
            if resposta.status_code != 200:
                log_callback(pedido, cnpj_planilha, "erro_api", resposta.status_code)
                continue
                
            dados_receita = resposta.json()
            
            # 1. Validação de CNAE Revenda
            cnae_principal = limpar_numeros(dados_receita.get('cnae_fiscal', ''))
            cnaes_empresa = [cnae_principal]
            for cnae_sec in dados_receita.get('cnaes_secundarios', []):
                cnaes_empresa.append(limpar_numeros(cnae_sec.get('codigo', '')))
            
            cnae_revenda_identificado = next((c for c in cnaes_empresa if c in CNAES_REVENDA), None)
            
            # 2. Captura e Padronização de Endereços (Planilha vs Receita)
            logradouro_plan = limpar_texto(linha.get('Logradouro', ''))
            numero_plan = limpar_texto(linha.get('Número', ''))
            cidade_plan = limpar_texto(linha.get('Cidade', ''))
            estado_plan = limpar_texto(linha.get('Estado', ''))
            cep_plan = limpar_numeros(linha.get('CEP', ''))
            
            tipo_via_rec = limpar_texto(dados_receita.get('tipo_logradouro', ''))
            nome_via_rec = limpar_texto(dados_receita.get('logradouro', ''))
            logradouro_rec = f"{tipo_via_rec} {nome_via_rec}".strip() if tipo_via_rec and tipo_via_rec not in nome_via_rec else nome_via_rec
            
            numero_rec = limpar_texto(dados_receita.get('numero', ''))
            cidade_rec = limpar_texto(dados_receita.get('municipio', ''))
            estado_rec = limpar_texto(dados_receita.get('uf', ''))
            cep_rec = limpar_numeros(dados_receita.get('cep', ''))
            
            # 3. Cruzamento Inteligente
            nucleo_plan = extrair_nucleo_logradouro(logradouro_plan)
            nucleo_rec = extrair_nucleo_logradouro(logradouro_rec)
            
            if nucleo_plan and nucleo_rec and (nucleo_plan in nucleo_rec or nucleo_rec in nucleo_plan):
                comp_logradouro = "IGUAL"
            else:
                comp_logradouro = "DIVERGENTE"
                
            comp_numero = "IGUAL" if numero_plan == numero_rec else "DIVERGENTE"
            comp_cidade = "IGUAL" if cidade_plan == cidade_rec else "DIVERGENTE"
            comp_estado = "IGUAL" if estado_plan == estado_rec else "DIVERGENTE"
            comp_cep = "IGUAL" if cep_plan == cep_rec else "DIVERGENTE"
            
            endereco_divergente = (
                comp_logradouro == "DIVERGENTE" or comp_numero == "DIVERGENTE" or
                comp_cidade == "DIVERGENTE" or comp_estado == "DIVERGENTE" or comp_cep == "DIVERGENTE"
            )
            
            # Pacotes de dados para a interface usar nos prints
            comparativo_tela = {
                "plan": f"{logradouro_plan}, {numero_plan} - {cidade_plan}/{estado_plan} (CEP: {cep_plan})",
                "rec": f"{logradouro_rec}, {numero_rec} - {cidade_rec}/{estado_rec} (CEP: {cep_rec})",
                "detalhes": f"Logradouro: {comp_logradouro} | Número: {comp_numero} | Cidade: {comp_cidade} | UF: {comp_estado} | CEP: {comp_cep}"
            }
            
            # 4. Aplicação das Regras de Negócio do Backoffice
            acao_back, pendencia, resolucao = "", "", ""
            
            if cnae_revenda_identificado:
                acao_back = "Cancelar Pedido - CNPJ revenda"
                pendencia = "CNPJ Revenda"
                resolucao = "Abrir ticket em massa"
                log_callback(pedido, cnpj_planilha, "revenda", cnae_revenda_identificado, comparativo_tela)
            elif endereco_divergente:
                acao_back = "Atualização de Endereço"
                pendencia = "PJ - Endereço divergente do SEFAZ"
                resolucao = "Abrir ticket em massa"
                log_callback(pedido, cnpj_planilha, "divergente", None, comparativo_tela)
            else:
                log_callback(pedido, cnpj_planilha, "regular", None, comparativo_tela)
                
            novas_linhas.append({
                "Pedido": pedido, 
                "CNPJ": cnpj_planilha, 
                "Ação Back": acao_back,
                "Pendência": pendencia, 
                "Resolução": resolucao
            })
            
        except Exception as e:
            log_callback(pedido, cnpj_planilha, "erro_geral", str(e))
            
    return novas_linhas
