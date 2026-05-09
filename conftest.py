# conftest.py — configuração do pytest para o projeto FSE Entrega 2
# Garante que a raiz do projeto está no sys.path para imports absolutos.

import sys
import os

# Adiciona a raiz do projeto ao path para permitir: from src.xxx import ...
sys.path.insert(0, os.path.dirname(__file__))
