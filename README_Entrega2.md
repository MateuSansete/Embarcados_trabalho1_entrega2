# Fundamentos de Sistemas Embarcados — Entrega 2
## Protocolos de Comunicação UART (Simplificado e MODBUS RTU)

Este projeto compõe a **Entrega 2** da disciplina de Fundamentos de Sistemas Embarcados da Universidade de Brasília. Ele implementa a comunicação serial via UART entre uma Raspberry Pi (Sistema Central) e um ESP32 (Nó Distribuído). O software foi desenhado para enviar os dados nos formatos de **Protocolo Simplificado Acadêmico** e **Protocolo MODBUS RTU Modificado**, com suporte a cálculo automático de CRC-16 e tratamento de exceções.

---

## 🛠 Requisitos e Dependências

- **Hardware:** Raspberry Pi conectada via barramento UART aos pinos TX/RX de um ESP32 (ou simulador do projeto).
- **Linguagem:** Python 3.10+
- **Bibliotecas:** 
  - `pyserial` (Responsável pelo manuseio das portas `/dev/serial0`)

### Instalação

Na raiz do repositório, garanta que as dependências do projeto estejam atualizadas executando:
```bash
pip install -r requirements.txt
```

---

##  Como Executar o CLI da UART

O módulo `uart_protocols` contém o CLI (Menu interativo) responsável pela execução dos testes e das chamadas pela UART. Ele deve ser executado a partir da **raiz do repositório**.

Abra o menu de comunicação utilizando o seguinte comando:
```bash
python3 -m src.uart_protocols.main
```

> **Dica:** O projeto possui um entry point global. Como a UART é o foco central desta entrega, o mesmo menu também pode ser invocado digitando apenas: `python3 -m src`

### Os 12 Comandos Requeridos
Uma vez no menu, você terá uma interface visual de terminal que lista 12 opções (6 para o protocolo simplificado e 6 para o Modbus RTU). Estes comandos permitem ler e escrever Inteiros, Floats e Strings na porta serial, validando completamente os requisitos de robustez do pacote.

---

##  Demonstração Visual (ThingsBoard)

Abaixo está o registro visual do funcionamento da aplicação integrada ao dashboard do **ThingsBoard**, onde enviamos dados e atualizamos interfaces IoT em tempo real.



![ThingsBoard Dashboard](./assets/thingsboard_widget_print.png)

---

## 🎥 Vídeo de Demonstração (Avaliação)

O vídeo abaixo demonstra de forma a execução da **Parte 1 e 2** exigidos, bem como a resposta dos componentes no ThingsBoard.

[🔗 Clique aqui para assistir à Demonstração da Entrega 2 no YouTube](https://youtu.be/yMJnIL8sqHY)

---

##  Estrutura da Entrega 2

```text
src/
├── __main__.py                      # Inicializador do CLI (Entry point do repositório)
├── common/
│   ├── exceptions/uart_exceptions.py# Exceções criadas (Timeouts, Modbus Error, etc)
│   └── hal/uart_controller.py       # Hardware Abstraction Layer para comunicação física
└── uart_protocols/                  # Módulo focado exclusivamente na Entrega 2
    ├── main.py                      # Interface do menu do terminal (Os 12 comandos)
    └── protocols/
        ├── simple_protocol.py       # Lógica e parsing do Protocolo Simplificado
        ├── modbus_protocol.py       # Lógica, empacotamento e parse do MODBUS RTU
        └── crc_utils.py             # Validador de redundância cíclica
```
