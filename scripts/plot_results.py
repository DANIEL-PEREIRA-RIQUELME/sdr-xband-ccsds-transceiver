import json
import os
import re
import matplotlib.pyplot as plt
import numpy as np

results_dir = "../output/results/test/"
artifact_dir = "/home/dan/.gemini/antigravity-cli/brain/0cc50d89-5175-4820-8949-3323578c8f2c"
ebn0s = [2.0, 2.8, 3.6, 4.4, 5.2, 6.0]

# --- 1. BER Curve ---
bers = []
for eb in ebn0s:
    diag_file = f"{results_dir}/diagnostic_results_{eb}.txt"
    sys_ber = 1.0
    if os.path.exists(diag_file):
        with open(diag_file, 'r') as f:
            for line in f:
                if "FER:" in line:
                    match = re.search(r'FER:\s+([0-9\.eE+-]+)', line)
                    if match:
                        sys_ber = float(match.group(1))
    bers.append(sys_ber)

plt.figure(figsize=(8,5))
plt.semilogy(ebn0s, bers, 'bo-')
plt.grid(True, which="both", ls="-")
plt.xlabel("Eb/N0 (dB)")
plt.ylabel("Bit Error Rate (BER)")
plt.title("Frame Error Rate vs Eb/N0")
plt.savefig(f"{artifact_dir}/ber_curve.png", dpi=150)
plt.close()

# --- 2. Doppler Curves ---
plt.figure(figsize=(10,6))
for eb in ebn0s:
    freq_file = f"{results_dir}/freqs_{eb}.json"
    if os.path.exists(freq_file):
        try:
            with open(freq_file, 'r') as f:
                freqs = json.load(f)
            # The freq updates every 'update_interval' samples.
            # At 25Msps, 131072 samples = 5.24 ms per update.
            # So x-axis is time in ms.
            time_ms = np.arange(len(freqs)) * 5.24
            plt.plot(time_ms, freqs, label=f"Eb/N0 = {eb} dB")
        except:
            pass

plt.xlabel("Time (ms)")
plt.ylabel("Estimated Doppler (Hz)")
plt.title("Coarse Doppler Sync Convergence")
plt.legend()
plt.grid(True)
plt.savefig(f"{artifact_dir}/doppler_curve.png", dpi=150)
plt.close()

# --- 3. CPU Performance Pie Chart ---
perf_file = "perf_metrics_promedio_10s.json"
if os.path.exists(perf_file):
    with open(perf_file, 'r') as f:
        perf = json.load(f)
    
    # We want "work time" or "cpu" metric.
    # Usually "work time" is the metric.
    work_times = {}
    for block, metrics in perf.items():
        for k, v in metrics.items():
            if "work time" in k:
                # remove gnuradio internals if desired
                bname = block.split('(')[0]
                work_times[bname] = v
                break

    if work_times:
        # Sort and take top 10
        sorted_blocks = sorted(work_times.items(), key=lambda x: x[1], reverse=True)
        labels = [x[0] for x in sorted_blocks[:10]]
        sizes = [x[1] for x in sorted_blocks[:10]]
        
        # Merge the rest into "Other"
        if len(sorted_blocks) > 10:
            other = sum(x[1] for x in sorted_blocks[10:])
            labels.append("Other")
            sizes.append(other)
            

        # Map blocks to descriptions
        descriptions = {
            'chess_coarse_doppler_sync': 'Doppler Sync (Corrección de Frecuencia Doppler)',
            'digital_costas_loop_cc': 'Costas Loop (Carrier Tracking & Phase Lock)',
            'chess_fast_sync': 'Fast Sync (ASM Framer & Ambiguity Resolution)',
            'ccsds_concatenated_rx': 'CCSDS RX (Hier Block interno)',
            'fec_extended_decoder': 'Viterbi Decoder (Decodificador Convolucional)',
            'satellites_decode_rs_ccsds': 'Reed-Solomon Decoder (Corrección de Errores FEC)',
            'digital_pfb_clock_sync_xxx': 'Polyphase Clock Sync (Symbol Timing Recovery)',
            'blocks_throttle2': 'Throttle (Limitador de Velocidad CPU)',
            'blocks_file_source': 'File Source (Lector del Archivo Binario TX)',
            'chess_downlink_channel': 'Downlink Channel (Simulador del Canal LEO)',
            'blocks_multiply_const_vxx': 'Multiply Const (Rotación de Fase de 90°)',
            'digital_constellation_soft_decoder_cf': 'Soft Decoder (Demodulación QPSK LLR)',
            'analog_agc_xx': 'AGC (Control Automático de Ganancia)'
        }
        
        mapped_labels = []
        for l in labels:
            base_name = re.sub(r'_[0-9]+$', '', l)
            base_name = re.sub(r'_[0-9]+$', '', base_name)
            desc = descriptions.get(base_name, None)
            if desc is None:
                # Try finding a partial match
                for key, val in descriptions.items():
                    if key in l:
                        desc = val
                        break
            if desc is None:
                desc = l
            
            # Combine name and function, handling long text
            if "(" in desc:
                name, func = desc.split("(")
                mapped_labels.append(f"{name.strip()}\n({func}")
            else:
                mapped_labels.append(desc)

        plt.figure(figsize=(12,12))
        plt.pie(sizes, labels=mapped_labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 9})
        plt.title("Consumo de CPU por Bloque (Top 10)")
        plt.tight_layout()

        plt.savefig(f"{artifact_dir}/cpu_pie.png", dpi=150)
        plt.close()

print("Plotting done.")
