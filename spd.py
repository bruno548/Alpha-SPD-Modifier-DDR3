import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

def calcular_crc16_core(buffer_bytes, tamanho_bloco, zerar_32_59=False):
    """Mecanismo base para cálculo do polinômio CRC-16 JEDEC (0x1021)."""
    buffer = bytearray(buffer_bytes[0:tamanho_bloco])
    
    if zerar_32_59 and tamanho_bloco >= 60:
        for i in range(32, 60):
            buffer[i] = 0x00

    crc = 0x0000
    for byte in buffer:
        crc = crc ^ (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return crc

class SPDModifierUniversalDDR3:
    def __init__(self, root):
        self.root = root
        self.root.title("Alpha Hardware - Modificador & Analisador Universal SPD DDR3 v3.6")
        self.root.geometry("980x680")
        
        self.spd_data = bytearray()
        
        # Variáveis de controle do motor adaptativo de CRC
        self.modo_crc_detectado = "Padrão JEDEC"
        self.tamanho_bloco_crc = 116
        self.mascarar_bytes_termicos = False
        self.b_low, self.b_high = 126, 127
        
        # Trava absoluta contra eventos fantasmas do Tkinter
        self.bloqueio_eventos = False
        
        self.criar_interface()

    def criar_interface(self):
        frame_topo = ttk.Frame(self.root, padding=10)
        frame_topo.pack(fill=tk.X)
        
        ttk.Button(frame_topo, text="Abrir Dump (.bin)", command=self.abrir_arquivo).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_topo, text="Salvar Dump Modificado", command=self.salvar_arquivo).pack(side=tk.LEFT, padx=5)
        
        self.lbl_arquivo_aberto = ttk.Label(frame_topo, text="Arquivo: Nenhum dump carregado", font=("Arial", 9, "italic"), foreground="gray")
        self.lbl_arquivo_aberto.pack(side=tk.LEFT, padx=15)
        
        frame_corpo = ttk.Frame(self.root, padding=10)
        frame_corpo.pack(fill=tk.BOTH, expand=True)
        
        self.frame_controles = ttk.LabelFrame(frame_corpo, text=" Análise e Configurações do Módulo ", padding=10)
        self.frame_controles.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Label(self.frame_controles, text="Identificação do Módulo", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        self.lbl_tecnologia = ttk.Label(self.frame_controles, text="Tecnologia: -")
        self.lbl_tecnologia.pack(anchor=tk.W, pady=2)
        
        self.lbl_capacidade = ttk.Label(self.frame_controles, text="Capacidade Calculada: -", font=("Arial", 9, "bold"))
        self.lbl_capacidade.pack(anchor=tk.W, pady=2)
        
        self.lbl_frequencia_atual = ttk.Label(self.frame_controles, text="Frequência Atual: -")
        self.lbl_frequencia_atual.pack(anchor=tk.W, pady=2)
        
        self.lbl_fabricante = ttk.Label(self.frame_controles, text="Fabricante: -")
        self.lbl_fabricante.pack(anchor=tk.W, pady=2)
        
        self.lbl_data_fab = ttk.Label(self.frame_controles, text="Data de Fabricação: -")
        self.lbl_data_fab.pack(anchor=tk.W, pady=2)
        
        self.lbl_serial = ttk.Label(self.frame_controles, text="Número de Série: -")
        self.lbl_serial.pack(anchor=tk.W, pady=2)
        
        ttk.Separator(self.frame_controles, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Label(self.frame_controles, text="Modificar Parâmetros", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(self.frame_controles, text="Alterar Densidade por Chip:").pack(anchor=tk.W, pady=(5, 2))
        self.combo_densidade = ttk.Combobox(self.frame_controles, values=["1 Gb", "2 Gb", "4 Gb", "8 Gb"], state="disabled")
        self.combo_densidade.pack(fill=tk.X, pady=3)
        self.combo_densidade.bind("<<ComboboxSelected>>", self.modificar_dados)
        
        ttk.Label(self.frame_controles, text="Alterar Frequência Máxima:").pack(anchor=tk.W, pady=(5, 2))
        self.combo_frequencia = ttk.Combobox(self.frame_controles, values=["1066 MHz", "1333 MHz", "1600 MHz"], state="disabled")
        self.combo_frequencia.pack(fill=tk.X, pady=3)
        self.combo_frequencia.bind("<<ComboboxSelected>>", self.modificar_dados)
        
        ttk.Label(self.frame_controles, text="Alterar Organização (Ranks):").pack(anchor=tk.W, pady=(5, 2))
        self.combo_ranks = ttk.Combobox(self.frame_controles, values=["1 Rank (Single)", "2 Ranks (Dual)"], state="disabled")
        self.combo_ranks.pack(fill=tk.X, pady=3)
        self.combo_ranks.bind("<<ComboboxSelected>>", self.modificar_dados)

        ttk.Separator(self.frame_controles, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Label(self.frame_controles, text="Assinatura & Integridade", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.lbl_crc_info = ttk.Label(self.frame_controles, text="Modo: Detectando...", font=("Arial", 9, "italic"))
        self.lbl_crc_info.pack(anchor=tk.W, pady=2)
        
        self.lbl_crc_status = ttk.Label(self.frame_controles, text="CRC: -", font=("Consolas", 10, "bold"))
        self.lbl_crc_status.pack(anchor=tk.W, pady=5)

        frame_hex = ttk.LabelFrame(frame_corpo, text=" Visualizador Hexadecimal (Bytes 0-127) ", padding=5)
        frame_hex.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.txt_hex = tk.Text(frame_hex, font=("Consolas", 10), wrap=tk.NONE)
        self.txt_hex.pack(fill=tk.BOTH, expand=True)

    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Binary Files", "*.bin"), ("All Files", "*.*")])
        if not caminho: return
        
        self.bloqueio_eventos = True
        
        with open(caminho, "rb") as f:
            self.spd_data = bytearray(f.read())
            
        if len(self.spd_data) < 128:
            messagebox.showerror("Erro", "O arquivo de dump deve ter pelo menos 128 bytes.")
            self.bloqueio_eventos = False
            return
            
        self.lbl_arquivo_aberto.config(text=f"Arquivo: {os.path.basename(caminho)}", foreground="black")
        
        self.analisar_assinatura_crc_universal()
        self.atualizar_painel()
        
        self.combo_densidade.config(state="readonly")
        self.combo_frequencia.config(state="readonly")
        self.combo_ranks.config(state="readonly")
        
        self.root.update_idletasks()
        self.bloqueio_eventos = False

    def analisar_assinatura_crc_universal(self):
        hipoteses = [
            {"tamanho": 117, "low": 126, "high": 127, "desc": "Kingston Estendido (117 Bytes)"},
            {"tamanho": 116, "low": 126, "high": 127, "desc": "JEDEC Longo Puro (116 Bytes)"},
            {"tamanho": 116, "low": 126, "high": 127, "desc": "JEDEC Longo Térmico (116 Bytes)", "mascara": True},
            {"tamanho": 62,  "low": 62,  "high": 63,  "desc": "JEDEC Curto Puro (62 Bytes)"},
            {"tamanho": 62,  "low": 62,  "high": 63,  "desc": "JEDEC Curto Térmico (62 Bytes)", "mascara": True}
        ]
        
        for h in hipoteses:
            l_off, h_off = h["low"], h["high"]
            crc_lido = self.spd_data[l_off] | (self.spd_data[h_off] << 8)
            usar_mascara = h.get("mascara", False)
            calc = calcular_crc16_core(self.spd_data, h["tamanho"], zerar_32_59=usar_mascara)
            
            if calc == crc_lido:
                self.b_low, self.b_high = l_off, h_off
                self.tamanho_bloco_crc = h["tamanho"]
                self.mascarar_bytes_termicos = usar_mascara
                self.modo_crc_detectado = h["desc"]
                return
                
        byte_0 = self.spd_data[0]
        if (byte_0 & 0x80) == 0:
            self.b_low, self.b_high = 126, 127
            self.tamanho_bloco_crc = 116
            self.modo_crc_detectado = "JEDEC Longo (Fallback)"
        else:
            self.b_low, self.b_high = 62, 63
            self.tamanho_bloco_crc = 62
            self.modo_crc_detectado = "JEDEC Curto (Fallback)"
        self.mascarar_bytes_termicos = False

    def extrair_metadados(self):
        tck = self.spd_data[12]
        map_freq = {0x12: "1066 MHz", 0x0C: "1333 MHz", 0x0A: "1600 MHz"}
        freq_str = map_freq.get(tck, f"Desconhecida ({tck:02X})")
        
        fab_id = (self.spd_data[117] << 8) | self.spd_data[118]
        map_fabricantes = {0x0198: "Kingston", 0x80AD: "Hynix", 0x859B: "Crucial", 0x00CE: "Samsung"}
        fab_str = map_fabricantes.get(fab_id, f"Desconhecido ({fab_id:04X})")
        
        try:
            ano = f"20{self.spd_data[120]:02X}" if self.spd_data[120] != 0 else "N/A"
            semana = f"{self.spd_data[121]:02X}" if self.spd_data[121] != 0 else "N/A"
            data_str = f"Semana {semana} de {ano}" if ano != "N/A" else "Não informada"
        except:
            data_str = "Erro na decodificação"
            
        serial_str = "".join(f"{b:02X}" for b in self.spd_data[122:126])
        return freq_str, fab_str, data_str, serial_str

    def calcular_capacidade_real(self):
        dens_bits = self.spd_data[4] & 0x0F
        mapeamento_densidade = {0x2: 128, 0x3: 256, 0x4: 512, 0x5: 1024}
        megabytes_por_chip = mapeamento_densidade.get(dens_bits, 0)
        
        byte_7 = self.spd_data[7]
        num_ranks = ((byte_7 >> 3) & 0x07) + 1
        largura_bits = 4 * (2 ** (byte_7 & 0x07))
        
        if largura_bits == 0 or megabytes_por_chip == 0:
            return "Erro no cálculo"
            
        chips_por_rank = 64 // largura_bits
        total_chips = chips_por_rank * num_ranks
        capacidade_gb = (total_chips * megabytes_por_chip) / 1024
        return f"{capacidade_gb:.2f} GB"

    def atualizar_painel(self):
        if not self.spd_data: return
        
        self.lbl_tecnologia.config(text="Tecnologia: DDR3 SDRAM" if self.spd_data[2] == 0x0B else f"Tecnologia: Não-DDR3 ({hex(self.spd_data[2])})")
        self.lbl_capacidade.config(text=f"Capacidade Calculada: {self.calcular_capacidade_real()}")
        
        freq_str, fab_str, data_str, serial_str = self.extrair_metadados()
        self.lbl_frequencia_atual.config(text=f"Frequência Atual: {freq_str}")
        self.lbl_fabricante.config(text=f"Fabricante: {fab_str}")
        self.lbl_data_fab.config(text=f"Data de Fabricação: {data_str}")
        self.lbl_serial.config(text=f"Número de Série: {serial_str}")
        
        dens_atual = self.spd_data[4] & 0x0F
        map_combo_dens = {0x2: "1 Gb", 0x3: "2 Gb", 0x4: "4 Gb", 0x5: "8 Gb"}
        self.combo_densidade.set(map_combo_dens.get(dens_atual, "Custom"))
        
        tck_atual = self.spd_data[12]
        map_combo_freq = {0x12: "1066 MHz", 0x0C: "1333 MHz", 0x0A: "1600 MHz"}
        self.combo_frequencia.set(map_combo_freq.get(tck_atual, "Custom"))
        
        ranks_atual = (self.spd_data[7] >> 3) & 0x07
        self.combo_ranks.set("1 Rank (Single)" if ranks_atual == 0 else "2 Ranks (Dual)")

        self.lbl_crc_info.config(text=f"Modo: {self.modo_crc_detectado}")
        
        crc_calculado = calcular_crc16_core(self.spd_data, self.tamanho_bloco_crc, self.mascarar_bytes_termicos)
        crc_lido = self.spd_data[self.b_low] | (self.spd_data[self.b_high] << 8)
        
        if crc_lido == crc_calculado:
            self.lbl_crc_status.config(text=f"CRC Lido/Calc: {crc_calculado:04X} (OK)", foreground="green")
        else:
            self.lbl_crc_status.config(text=f"CRC Lido: {crc_lido:04X} | Calc: {crc_calculado:04X} (ALTERADO)", foreground="blue")
            
        self.txt_hex.config(state=tk.NORMAL)
        self.txt_hex.delete("1.0", tk.END)
        self.txt_hex.insert(tk.END, "Offset  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\n" + "-" * 56 + "\n")
        
        for i in range(0, 128, 16):
            linha = self.spd_data[i:i+16]
            hex_bytes = " ".join(f"{b:02X}" for b in linha)
            self.txt_hex.insert(tk.END, f"{i:06X}  {hex_bytes}\n")
        self.txt_hex.config(state=tk.DISABLED)

    def modificar_dados(self, event):
        if not self.spd_data or self.bloqueio_eventos: return
        
        # 1. Modifica Densidade (Byte 4)
        map_dens_rev = {"1 Gb": 0x02, "2 Gb": 0x03, "4 Gb": 0x04, "8 Gb": 0x05}
        sel_dens = self.combo_densidade.get()
        if sel_dens in map_dens_rev:
            self.spd_data[4] = (self.spd_data[4] & 0xF0) | map_dens_rev[sel_dens]
            
        # 2. Modifica Frequência (Byte 12)
        map_freq_rev = {"1066 MHz": 0x12, "1333 MHz": 0x0C, "1600 MHz": 0x0A}
        sel_freq = self.combo_frequencia.get()
        if sel_freq in map_freq_rev:
            self.spd_data[12] = map_freq_rev[sel_freq]
            
        # 3. Modifica Ranks (Byte 7) - Preservando os bits de coluna baixos
        sel_ranks = self.combo_ranks.get()
        if "1 Rank" in sel_ranks:
            self.spd_data[7] = (self.spd_data[7] & 0xC7) | (0x00 << 3)
        elif "2 Ranks" in sel_ranks:
            self.spd_data[7] = (self.spd_data[7] & 0xC7) | (0x01 << 3)

        # Recalcula o CRC mantendo a assinatura Kingston de 117 bytes detectada
        novo_crc = calcular_crc16_core(self.spd_data, self.tamanho_bloco_crc, self.mascarar_bytes_termicos)
        
        self.spd_data[self.b_low] = novo_crc & 0xFF
        self.spd_data[self.b_high] = (novo_crc >> 8) & 0xFF
        
        self.atualizar_painel()

    def salvar_arquivo(self):
        if not self.spd_data: return
        caminho = filedialog.asksaveasfilename(defaultextension=".bin", filetypes=[("Binary Files", "*.bin")])
        if caminho:
            with open(caminho, "wb") as f:
                f.write(self.spd_data)
            messagebox.showinfo("Sucesso", "Firmware atualizado e salvo com sucesso!")

if __name__ == "__main__":
    root = tk.Tk()
    app = SPDModifierUniversalDDR3(root)
    root.mainloop()