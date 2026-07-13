# Alpha Hardware - Modificador & Analisador Universal SPD DDR3

Este repositório contém o código-fonte (`spd.py`) e o executável compilado (`AH_APD.exe`) de uma ferramenta especializada em análise, diagnóstico e modificação física de firmware **SPD (Serial Presence Detect)** de módulos de memória **DDR3 SDRAM**. 

O software foi projetado para auxiliar técnicos de laboratório e engenheiros de hardware a reconfigurar os parâmetros lógicos gravados na EEPROM das memórias, solucionando problemas de compatibilidade e viabilizando o reaproveitamento de componentes.

---

## 🚀 Motivação: Por que modificar o SPD de uma memória?

No diagnóstico de bancada e manutenção de hardware, existem cenários críticos onde a reprogramação ou modificação lógica do SPD se faz necessária para o reparo e reaproveitamento de módulos:

1. **Isolamento de Ranks por Hardware (Principal Aplicação):** Se um pente de memória é Dual Rank (possui duas linhas lógicas de controle, geralmente com chips soldados em ambos os lados do PCB) e um dos chips de um lado apresenta defeito, o software permite rebaixar o módulo para **1 Rank (Single)**. Isso desativa eletronicamente o mapeamento de toda a partição defeituosa. O controlador da placa-mãe passa a ignorar aqueles endereços físicos, permitindo que o pente volte a dar vídeo e funcione perfeitamente com metade da capacidade original, mas 100% estável.
2. **Adequação de Densidade para Compatibilidade:** Permite alterar o mapa de densidade de Gigabits por chip (Byte 4) para adequar o reconhecimento do circuito lógico em placas-mãe antigas que não possuem suporte a matrizes de alta densidade, evitando o sintoma de "Sem Vídeo" ou loops de reinicialização.
3. **Underclocking Nativo para Estabilização:** Força o barramento a trabalhar em frequências menores (ex: reduzir de 1600 MHz para 1333 MHz ou 1066 MHz) diretamente no firmware. Isso diminui o estresse físico nos chips restantes e sana problemas crônicos de tela azul (BSOD) causados por degradação do silício.

---

## 🧠 Princípios por Trás do Software

### O Motor de Correção de CRC JEDEC e a Variante Kingston
O padrão global estabelecido pela JEDEC estipula que a integridade dos dados contidos nos primeiros blocos do SPD deve ser validada por uma verificação de redundância cíclica de 16 bits (Polinômio CRC-16 JEDEC `0x1021`). Se um único bit for alterado (como a frequência ou densidade) sem que o CRC seja recalculado, a placa-mãe rejeitará o pente de memória, resultando em ausência de vídeo.

* **Descoberta do Padrão Kingston (117 Bytes):** Enquanto memórias comuns utilizam o bloco padrão de 116 bytes para o cálculo, esta versão traz embarcado o motor matemático específico que decodificou a assinatura estendida da Kingston, que estende o bloco de integridade por mais 1 byte (117 bytes totais). Isso garante **100% de precisão e validação verde** ao alterar dumps de módulos proprietários dessa fabricante.

### Densidade vs. Capacidade Total
A capacidade total de um módulo DDR3 não é um valor absoluto gravado diretamente. Ela é o produto final de uma equação física lida pelo controlador de memória baseada no **Byte 4** (Densidade por chip em Gigabits) e no **Byte 7** (Organização de Ranks e barramento). O software calcula essa matriz em tempo real, evitando que o usuário aplique configurações impossíveis para o circuito eletrônico correspondente.

---

## 🛠️ Como Utilizar o Sistema

1. **Baixar o Software:** Você pode utilizar o script bruto rodando `python spd.py` (necessita do Tkinter instalado) ou executar diretamente o arquivo independente **`AH_APD.exe`**.
2. **Carregar o Dump:** Faça a extração física do arquivo `.BIN` do chip EEPROM do seu pente de memória usando um gravador de bancada (ex: CH341A, RT809F, TL866) e clique em **"Abrir Dump (.bin)"**.
3. **Modificar Parâmetros:** * Para reduzir a capacidade de um módulo de 4GB Dual Rank para 2GB, por exemplo, altere a **Densidade por Chip** para `1 Gb`, mantendo os `2 Ranks (Dual)` intocados para não quebrar o endereçamento físico do circuito.
4. **Salvar e Gravar:** Clique em **"Salvar Dump Modificado"**. O novo arquivo gerado já virá com todos os bytes recalculados e a assinatura de CRC perfeitamente corrigida. Basta gravá-lo de volta na memória.

---

## 📋 Especificações Base e Referências Técnicas

Este utilitário foi desenvolvido em estrita conformidade com os mapas de registradores e especificações de engenharia da **JEDEC**:
* Os padrões de mapeamento dos Bytes 0 a 127 de temporização, barramento e organização foram baseados no documento oficial: **[JEDEC Standard No. 21-C - Annex K: Serial Presence Detect (SPD) for DDR3 SDRAM Modules](https://www.jedec.org/standards-documents/docs/jesd21c)**.

> 📌 **Nota de Versão:** A presente versão do software é especializada no padrão **DDR3**. Arquiteturas de expansão de blocos e cálculo estrutural para **DDR4** estão planejadas para cronogramas e atualizações de versões futuras.

---

## ⚖️ Licença (GNU GPLv3)

Este projeto é software livre e está licenciado sob a **GNU General Public License v3.0**. 
* **Você pode:** Usar, copiar, modificar e distribuir este software de forma totalmente gratuita.
* **Condição Obrigatória (Copyleft):** Qualquer software gerado, modificado ou derivado deste código deve, obrigatoriamente, ser mantido sob os mesmos termos desta licença, com código-fonte aberto e distribuição gratuita.

---
*Desenvolvido com maestria silenciosa por **Alpha Hardware**.*
