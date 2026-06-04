# v7_streamlit
Código usado para validar se um CNPJ é revenda, compara os endereços e cria uma planilha com os resultados.

Os pedidos são gerados no Hybris Admin Console e extraídos para uma base de dados em uma planilha excel, juntando código do pedido, CNPJ, endereço cadastrado, entre outros. 

O código pega esses dados da planilha, compara se um CNPJ é revenda, baseado no CNAE principal e secundário, compara se o endereço cadastrado da base é igual ao endereço da receita federal (usando api brasil) e cria uma nova planilha com os resultados.
