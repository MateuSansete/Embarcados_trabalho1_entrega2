# Sistema de Controle de Semáforos — Entrega 1

Este projeto implementa um sistema de controle de semáforos concorrente para Raspberry Pi, desenvolvido para a disciplina de Fundamentos de Sistemas Embarcados (2026/1). O sistema gerencia dois modelos de cruzamentos simultaneamente através de multi-threading e máquinas de estado.

## Requisitos

- **Hardware**: Raspberry Pi (pinagem BCM).
- **Linguagem**: Python 3.10+.
- **Bibliotecas**: `RPi.GPIO` (para interação com hardware).

## Instalação

1. Clone o repositório para sua Raspberry Pi.
2. Certifique-se de ter o Python 3 e o gerenciador de pacotes `pip` instalados.
3. Instale as dependências necessárias:

```bash
pip install -r requirements.txt
```

## Instruções de Execução

O sistema deve ser executado como um módulo Python a partir da raiz do projeto.

### Executar ambos os modelos (Padrão)

Inicia o Modelo 1 (Semáforo Simples) e o Modelo 2 (Cruzamento Completo) em paralelo:

```bash
python3 -m src.main
```

### Executar modelos individualmente

Caso deseje testar apenas um dos cruzamentos:

- **Modelo 1 apenas**:
  ```bash
  python3 -m src.main --modelo 1
  ```

- **Modelo 2 apenas**:
  ```bash
  python3 -m src.main --modelo 2
  ```

## Estrutura do Projeto

```
src/
├── __init__.py                  # Pacote raiz
├── __main__.py                  # Entry point (python3 -m src)
├── main.py                      # Controlador principal (threads + sinais)
│
├── config/                      # Sub-pacote de configuração
│   ├── __init__.py              # Re-exporta constantes
│   └── settings.py              # Pinos GPIO, tempos, debounce
│
├── hal/                         # Sub-pacote HAL (Hardware Abstraction Layer)
│   ├── __init__.py              # Re-exporta GPIOController
│   └── gpio_controller.py       # Abstração GPIO (leitura, escrita, callbacks)
│
└── models/                      # Sub-pacote de modelos de semáforo
    ├── __init__.py              # Re-exporta modelos
    ├── traffic_light_model1.py  # Modelo 1 — Semáforo Simples (3 LEDs)
    └── traffic_light_model2.py  # Modelo 2 — Cruzamento Completo (3 bits)
```

## Encerramento Seguro

O programa trata sinais `SIGINT` (Ctrl+C). Ao encerrar:
1. Cada modelo desliga seus LEDs (saídas em LOW).
2. Os event_detect dos botões são removidos.
3. **Não** é usado `GPIO.cleanup()` — os pinos permanecem em seus modos configurados (OUTPUT LOW ou INPUT com pull-down), evitando que fiquem em estado flutuante (alta impedância).
