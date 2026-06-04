# Backoffice: Validador FULL 2.0

Utilizada para identificar tanto as revendas quanto os clientes que preencheram o endereço de entrega divergente do cadastro oficial do SEFAZ/Receita Federal, evitando problemas fiscais.

O que ele faz:
1. Recebe a planilha de pedidos extraída do sistema Hybris.
2. Consulta a base de dados da Receita Federal pela Brasil API.
3. Executa um algoritmo de comparação inteligente por aproximação (núcleo do logradouro) entre o endereço que veio da base de dados e o endereço oficial da BrasilAPI.
4. Classifica e escreve na planilha os pedidos irregulares.
5. Exibe na tela do navegador se os pedidos aprovados e negados, indicando qual é a divergência de dados.
