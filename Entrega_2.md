# Entrega 2 — Comunicação UART (Protocolo Simplificado + MODBUS Modificado)

Trabalho 1 — Entrega 2 da disciplina de **Fundamentos de Sistemas Embarcados (2026/1)**

## 1. Objetivos

Implementar, na **Raspberry Pi**, dois protocolos de comunicação serial UART com a **ESP32**:

- **Parte 1** — Protocolo **simplificado** (sem MODBUS, sem CRC), com 6 comandos de solicitação e envio de dados.
- **Parte 2** — Wrapper **MODBUS modificado**, baseado no [`uart_modbus.md`](https://gitlab.com/fse_fga/raspberry-pi/exercicios/exercicio-2-uart-modbus), com matrícula expandida para os **6 últimos dígitos** ao invés dos 4 originais.

A dispositivo conectado à UART responde aos dois protocolos **simultaneamente** na mesma UART. 

A visualização dos comandos recebidos pelo dispositivo pode ser feita pelo dashboard **uart** no ThingsBoard que mostra cada comando em tempo real, identifica o protocolo de origem e destaca a matrícula.


![UART](./figuras/Dashboard_UART.png)  


## 2. Configuração da UART

| Parâmetro            | Valor    |
|----------------------|----------|
| Baudrate             | 115200   |
| Paridade             | Nenhuma  |
| Bits de dados        | 8        |
| Bits de parada       | 1        |
| Controle de fluxo    | Nenhum   |

A porta UART utilizada na Raspberry Pi para comunicação com a ESP32 é definida no laboratório (geralmente `/dev/ttyS0` ou `/dev/serial0`).

> **Atenção:** o byte de matrícula é o valor **inteiro** do dígito (0–9), e **não** o caractere ASCII correspondente. Ou seja, o dígito `6` é transmitido como o byte `0x06`, não como `0x36`.

# Parte 1 — Protocolo Simplificado

Protocolo enxuto, sem endereçamento de dispositivo e sem CRC. Cada pacote começa com o byte de **comando** seguido do payload e da **matrícula de 6 dígitos** (6 últimos dígitos). O dispositivo responde imediatamente com bytes brutos no formato definido para cada comando.

## 1.1 Comandos de solicitação de informações

Pacote enviado pela RPi → Dispositivo:

```
[CMD][D1][D2][D3][D4][D5][D6]
```

onde `[D1]..[D6]` são os 6 últimos dígitos da matrícula em bytes brutos (0–9).

Exemplo para a matrícula `654321`: `0xA1 0x06 0x05 0x04 0x03 0x02 0x01` (7 bytes).

| Comando | Significado                  | Resposta do dispositivo                                          |
|:-------:|------------------------------|------------------------------------------------------------|
| `0xA1`  | Solicita inteiro             | 4 bytes (`int32_t` little-endian) — **valor constante**    |
| `0xA2`  | Solicita float               | 4 bytes (`float` little-endian) — **valor constante**      |
| `0xA3`  | Solicita string              | 1 byte de tamanho (`N`) seguido de `N` bytes — **string constante** |

## 1.2 Comandos de envio de informações

Pacote enviado pela RPi → Dispositivo:

| Comando | Estrutura do pacote                                          | Tamanho        |
|:-------:|--------------------------------------------------------------|:--------------:|
| `0xB1`  | `[0xB1][int32 LE: 4 bytes][6 dígitos da matrícula]`          | 11 bytes       |
| `0xB2`  | `[0xB2][float LE: 4 bytes][6 dígitos da matrícula]`          | 11 bytes       |
| `0xB3`  | `[0xB3][N: 1 byte][string: N bytes][6 dígitos da matrícula]` | `8 + N` bytes  |

Resposta do dispositivo:

| Comando | Resposta                                                                  |
|:-------:|---------------------------------------------------------------------------|
| `0xB1`  | 4 bytes: `int_recebido * último_dígito_da_matrícula`                      |
| `0xB2`  | 4 bytes: `float_recebido * último_dígito_da_matrícula`                    |
| `0xB3`  | 1 byte de tamanho seguido da string `"Resposta da UART: " + string_enviada` |

> O **último dígito** da matrícula é o **menos significativo** (no exemplo `654321`, é `1`).

## 1.3 Erros de sintaxe

Se o dispositivo receber um byte de comando fora da faixa válida, ela publica um evento de erro no widget e descarta o pacote. A RPi deve detectar timeout ao não receber a resposta esperada e logar o erro.

# Parte 2 — Wrapper MODBUS Modificado

A Parte 2 segue a especificação completa do [`uart_modbus.md`](./uart_modbus.md), com **uma única diferença**:

> **A matrícula passa a ter 6 dígitos** (os 6 últimos da matrícula do aluno) em vez dos 4 dígitos originais. Todos os pacotes que incluíam matrícula no MODBUS agora têm **2 bytes a mais** entre o payload e o CRC-16.

Todo o restante (endereçamento, código de função, CRC-16, fluxo cliente/servidor) permanece **idêntico** ao descrito em `uart_modbus.md`.

## 2.1 Formato genérico atualizado

| *A.* Endereço | *B.* Função | *C.* Sub-código + dados | *D.* Matrícula | *E.* CRC-16 |
|:-:|:-:|:-:|:-:|:-:|
| 1 byte | 1 byte | n bytes | **6 bytes** | 2 bytes |

## 2.2 Lista de códigos (mesma da Tabela 1 de `uart_modbus.md`)

| Código | Sub-código | Solicitação                          | Mensagem de Retorno                                  |
|:------:|:----------:|--------------------------------------|------------------------------------------------------|
| `0x23` | `0xA1`     | Solicita inteiro (`int32`)           | `int` (4 bytes)                                      |
| `0x23` | `0xA2`     | Solicita float                       | `float` (4 bytes)                                    |
| `0x23` | `0xA3`     | Solicita string                      | `[len: 1 byte][string: len bytes]`                   |
| `0x16` | `0xB1`     | Envia inteiro                        | `int` (4 bytes)                                      |
| `0x16` | `0xB2`     | Envia float                          | `float` (4 bytes)                                    |
| `0x16` | `0xB3`     | Envia string                         | `[len: 1 byte][string: len bytes]`                   |

## 2.3 Exemplos de pacotes (matrícula `654321`)

**Solicita inteiro** (`0x01 0x23 0xA1 + matrícula + CRC`)

```
0x01 0x23 0xA1 0x06 0x05 0x04 0x03 0x02 0x01 [CRC_LO] [CRC_HI]
                ^─────── 6 dígitos ────────^
Total: 11 bytes (3 + 6 + 2)
```

**Envia inteiro `3245`** (`0x01 0x16 0xB1 + 4 bytes int + matrícula + CRC`)

```
0x01 0x16 0xB1 0xAD 0x0C 0x00 0x00 0x06 0x05 0x04 0x03 0x02 0x01 [CRC_LO] [CRC_HI]
                ^── int LE ──^   ^─────── 6 dígitos ────────^
Total: 15 bytes (3 + 4 + 6 + 2)
```

**Envia string `"oi"`** (`0x01 0x16 0xB3 + len + str + matrícula + CRC`)

```
0x01 0x16 0xB3 0x02 'o' 'i' 0x06 0x05 0x04 0x03 0x02 0x01 [CRC_LO] [CRC_HI]
                ^len^ ^str^ ^─────── 6 dígitos ────────^
Total: 14 bytes (3 + 1 + 2 + 6 + 2)
```

## 2.4 Diferenças explícitas em relação ao `uart_modbus.md`

| Aspecto                                | Original | Esta Entrega |
|----------------------------------------|:--------:|:------------:|
| Bytes de matrícula                     | 4        | **6**        |
| Tamanho do pacote `solicita INT/FLOAT/STRING` (até CRC, exclusive) | 7 bytes  | **9 bytes**  |
| Tamanho do pacote `envia INT/FLOAT` (até CRC, exclusive)            | 11 bytes | **13 bytes** |
| Tamanho do pacote `envia STRING` (até CRC, exclusive)               | `8 + N`  | **`10 + N`** |
| Endereçamento, CRC-16, códigos         | iguais   | iguais       |

## 2.5 Requisitos da Parte 2

1. Reaproveitar a estrutura da Parte 1, adicionando o wrapper MODBUS (endereço, função, sub-código, CRC-16) em torno de cada comando.
2. **Calcular e validar o CRC-16** (mesmo polinômio do `uart_modbus.md` — código de referência em [`main/crc16.c`](../main/crc16.c) e equivalente Python em [`raspberry_pi_test_code/crc16.py`](../raspberry_pi_test_code/crc16.py)).
3. Tratar respostas com **bit de erro** (função com MSB setado) e o respectivo código de exceção.
4. Menu único na CLI deve permitir escolher **qual protocolo usar** (simplificado ou MODBUS) antes de cada comando, ou alternativamente disponibilizar dois sub-menus.
5. Imprimir em tela todos os bytes enviados/recebidos e os campos decodificados.


## 4. Requisitos Gerais

1. Linguagem: **Python**, **C/C++** ou **Rust**.
2. Cada operação deve imprimir em tela toda a sequência de bytes (envio e resposta) — **não vale apenas mostrar o valor decodificado**.
3. Tratamento adequado de erros: timeout, CRC inválido (Parte 2), comando desconhecido, byte de tamanho fora do range.
4. Fornecer **Makefile** (C/C++) ou **requirements.txt** (Python) e instruções de execução no `README`.
5. O código deve ser estruturado em **funções independentes**, uma por comando, mais utilitários (`enviar_pacote`, `ler_resposta`, `calcular_crc`, etc.).
6. As duas Partes devem coexistir no mesmo executável da Raspberry Pi (ou em executáveis irmãos com README explicando a estrutura).

## 5. Critérios de Avaliação

| Item                                                                  | Peso |
|-----------------------------------------------------------------------|:----:|
| Parte 1 — todos os 6 comandos funcionando corretamente                | 40 % |
| Parte 2 — todos os 6 comandos funcionando com CRC correto e matrícula de 6 dígitos | 60 % |

## 6. Entregáveis

- Commit no repositório com a Tag: "Entrega 2".
- Vídeo curto (até 5 min) demonstrando a execução dos 12 comandos (6 + 6) e o widget do ThingsBoard recebendo os eventos em tempo real.
- README com instruções de build/execução e print da matrícula em destaque no widget.

## 7. Referências

- Especificação completa do MODBUS adaptado: [`uart_modbus.md`](https://gitlab.com/fse_fga/raspberry-pi/exercicios/exercicio-2-uart-modbus).