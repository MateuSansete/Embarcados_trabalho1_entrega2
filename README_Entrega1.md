# Fundamentos de Sistemas Embarcados — Entrega 1
## Sistema Concorrente de Controle de Semáforos

Este projeto compõe a **Entrega 1** da disciplina de Fundamentos de Sistemas Embarcados da Universidade de Brasília. Ele implementa um sistema de controle de tráfego de semáforos rodando em uma Raspberry Pi. O sistema lida com cruzamentos de vias (luzes para carros) e faixas de pedestres usando GPIO, além de interagir fisicamente com botões, operando de forma 100% concorrente através de *threads*.

---

## 🛠 Requisitos e Hardware

- **Hardware:** Raspberry Pi configurada utilizando a pinagem BCM.
- **Linguagem:** Python 3.10+
- **Bibliotecas Necessárias:** 
  - `RPi.GPIO` (Fundamental para o controle de sinais digitais de entrada e saída)

---

## 🚀 Instalação e Configuração

1. Faça o clone do repositório para o sistema da sua Raspberry Pi.
2. Certifique-se de estar na raiz do diretório do projeto.
3. Instale os requerimentos do sistema (que já incluem bibliotecas da Entrega 2, mas contemplam a da Entrega 1):
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚥 Como Executar

O sistema foi empacotado em um módulo chamado `traffic_system` e deve ser executado a partir da **raiz do projeto**. 

Para iniciar o sistema de trânsito em sua versão completa:

```bash
python3 -m src.traffic_system
```

### Isolando a Execução por Modelo
Se, para fins de teste ou demonstração, você desejar rodar o controle sobre apenas um cruzamento específico, você pode utilizar as flags criadas na inicialização do sistema:

- **Apenas o Cruzamento 1:**
  ```bash
  python3 -m src.traffic_system --modelo 1
  ```
- **Apenas o Cruzamento 2:**
  ```bash
  python3 -m src.traffic_system --modelo 2
  ```

---

## 📁 Estrutura da Entrega 1

```text
src/
└── traffic_system/                  # Módulo focado exclusivamente na Entrega 1
    ├── __main__.py                  # Facilita a chamada direta via 'python3 -m'
    ├── main.py                      # Instanciação das Threads e do Loop principal
    └── models/                      # Definição e lógicas de estado das vias e pedestres
```
