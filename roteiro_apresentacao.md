# Roteiro de Apresentação - Entrega 2 (FSE)

**Tempo estimado total:** ~2 minutos e 30 segundos
**Objetivo:** Demonstração técnica da arquitetura, protocolos (Simplificado e Modbus) e integração com ThingsBoard.

---

### 1. Introdução e objetivo do trabalho (0:00 - 0:15)
- **Tempo estimado:** 15 segundos
- **Ação na tela:** Câmera no rosto (opcional) ou slide/tela de título com seu nome, matrícula (062240) e nome da disciplina. Transição rápida para a tela do terminal.
- **Texto a ser narrado:** 
  > "Olá, meu nome é Mateus, matrícula zero, seis, dois, dois, quatro, zero. Este vídeo apresenta a Entrega 2 da disciplina de Fundamentos de Sistemas Embarcados. O objetivo do projeto é estabelecer uma comunicação UART confiável entre a Raspberry Pi e a ESP32, fazendo coexistir dois protocolos distintos na mesma aplicação."
- **Pontos técnicos a destacar:** Identificação do aluno, tecnologias (Raspberry, ESP32, UART).

### 2. Explicação da arquitetura do projeto (0:15 - 0:30)
- **Tempo estimado:** 15 segundos
- **Ação na tela:** Exibir no editor de código (ex: VS Code) a árvore de arquivos, expandindo a pasta `src`. Destacar rapidamente os arquivos `uart_controller.py`, `simple_protocol.py` e `modbus_protocol.py`.
- **Texto a ser narrado:** 
  > "O projeto foi estruturado em Python seguindo uma arquitetura modular. A camada física foi isolada no controlador UART, enquanto as lógicas de empacotamento ficaram divididas entre os módulos do protocolo simplificado e do Modbus. Cálculos de validação e tratamento de exceções também foram modularizados para garantir o baixo acoplamento e facilitar a manutenção."
- **Pontos técnicos a destacar:** Arquitetura modular, separação de responsabilidades (HAL vs Protocolos).

### 3. Demonstração do menu principal (0:30 - 0:40)
- **Tempo estimado:** 10 segundos
- **Ação na tela:** No terminal, executar o projeto (`python src/main.py` ou similar). Mostrar o menu interativo aparecendo na tela com todas as opções.
- **Texto a ser narrado:** 
  > "Ao executar a aplicação principal, inicializamos a porta serial a cento e quinze mil e duzentos bauds, sem paridade e com um stop bit. Na tela, temos um menu único que permite disparar os doze comandos exigidos: seis do protocolo da Parte 1 e seis do Modbus da Parte 2."
- **Pontos técnicos a destacar:** Configuração da UART (115200 8N1), menu único para os 12 comandos.

### 4. Demonstração rápida do protocolo simplificado (0:40 - 0:55)
- **Tempo estimado:** 15 segundos
- **Ação na tela:** Selecionar no menu uma opção do Protocolo Simplificado (ex: Solicitar inteiro). Mostrar a resposta no terminal. Depois, enviar um float.
- **Texto a ser narrado:** 
  > "Começando pela Parte 1, o protocolo simplificado. Ao solicitar ou enviar um dado, a requisição é empacotada e transmitida. Podemos visualizar no terminal a impressão imediata de todos os bytes brutos que são enviados pela Raspberry e a resposta em hexadecimal recebida da ESP32."
- **Pontos técnicos a destacar:** Impressão de bytes brutos enviados e recebidos no terminal.

### 5. Explicação detalhada do MODBUS modificado (0:55 - 1:15)
- **Tempo estimado:** 20 segundos
- **Ação na tela:** Mostrar rapidamente o arquivo `uart_modbus.md` (ou um diagrama caso possua) evidenciando a estrutura do frame Modbus modificado.
- **Texto a ser narrado:** 
  > "Para a Parte 2, implementamos um protocolo base Modbus RTU, com uma modificação. Cada frame transmitido contém o endereço do dispositivo, o código da função, o payload de dados e, obrigatoriamente, seis bytes correspondentes ao valor numérico da minha matrícula. Por fim, o frame é fechado com dois bytes de validação CRC."
- **Pontos técnicos a destacar:** Estrutura do frame, inclusão mandatória de 6 bytes da matrícula.

### 6. Demonstração dos comandos MODBUS (1:15 - 1:40)
- **Tempo estimado:** 25 segundos
- **Ação na tela:** Retornar ao terminal. Executar comandos Modbus do menu (ex: solicitar string e enviar float). Selecionar/marcar com o mouse a sequência dos 6 bytes da matrícula no pacote impresso no log.
- **Texto a ser narrado:** 
  > "Ao executarmos um comando Modbus, notem a expansão do pacote transmitido. Nesta parte do log, podemos identificar exatamente os bytes da minha matrícula: zero zero, zero seis, zero dois, zero dois, zero quatro, zero zero. Ela está embutida no pacote como valores brutos, imediatamente antes do CRC de validação."
- **Pontos técnicos a destacar:** Comprovação visual dos 6 bytes da matrícula nos frames (00 06 02 02 04 00).

### 7. Explicação do CRC-16 (1:40 - 1:55)
- **Tempo estimado:** 15 segundos
- **Ação na tela:** Manter a tela no log do terminal, apontando para os dois últimos bytes do pacote. Mostrar brevemente o arquivo `crc_utils.py` com a lógica implementada.
- **Texto a ser narrado:** 
  > "A integridade dos dados na Parte 2 é garantida pelo cálculo rigoroso do CRC-16, utilizando o polinômio zero xis A zero zero um e semente inicial zero xis F F F F. O hash é processado em little-endian. O sistema possui tratamento de erros e timeout, lidando com respostas corrompidas ou falhas na ESP32 sem comprometer a execução."
- **Pontos técnicos a destacar:** Polinômio 0xA001, inicial 0xFFFF, little-endian, tratamento customizado de exceções (CRC e Timeout).

### 8. Demonstração do dashboard UART no ThingsBoard (1:55 - 2:15)
- **Tempo estimado:** 20 segundos
- **Ação na tela:** Dividir a tela (ou alternar rapidamente) entre o terminal e o navegador com o ThingsBoard. Solicitar dados no terminal e mostrar o dashboard atualizando.
- **Texto a ser narrado:** 
  > "Avançando, todo este fluxo de comunicação UART está integrado ao ThingsBoard. Os dados obtidos nas leituras, seja temperatura ou status do sistema, são publicados de forma automática. Assim que uma resposta serial válida é processada, vemos o dashboard em nuvem atualizar em tempo real."
- **Pontos técnicos a destacar:** Integração com plataforma cloud, atualização em tempo real através dos dados recebidos via UART.

### 9. Conclusão final (2:15 - 2:30)
- **Tempo estimado:** 15 segundos
- **Ação na tela:** Encerrar a execução no terminal de forma limpa. Mostrar o arquivo `requirements.txt` aberto no editor e, logo em seguida, o início do `README.md`.
- **Texto a ser narrado:** 
  > "O controle de dependências está formalizado no arquivo requirements, e as instruções de uso estão detalhadas no README. Cumprimos todos os requisitos estabelecidos para a Entrega 2, entregando uma solução estável e funcional. Agradeço a atenção e até mais."
- **Pontos técnicos a destacar:** Arquivo requirements.txt, arquivo README instrucional, encerramento limpo da solução.
