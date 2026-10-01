"""Camada analitica (RF-05): calculos estatisticos com NumPy.

Funcoes puras que recebem listas/arrays e devolvem numeros: nao conhecem
banco, HTTP nem FastAPI. As rotas buscam os dados e chamam estas funcoes
(separacao exigida pelo RNF-04). Os calculos usam operacoes vetorizadas do
NumPy (RNF-01), sem lacos Python sobre os pontos.
"""
