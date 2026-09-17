#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local CPU Profiler for GNU Radio Transceiver Pipeline
=====================================================
Samples per-thread CPU utilization to identify block-by-block bottlenecks
across the multi-threaded SDR architecture.

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""
import os
import sys
import glob
import time
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SIM_SCRIPT = SCRIPTS_DIR / "benchmark_local_speed.py"

env = os.environ.copy()
env["PYTHONPATH"] = f"/usr/lib/python3/dist-packages:{os.path.expanduser('~/.local/state/gnuradio')}:{str(PROJECT_ROOT / 'flowgraphs')}"
env["LD_LIBRARY_PATH"] = f"/home/dan/.local/lib/x86_64-linux-gnu:/home/dan/.local/lib:/usr/local/lib:/usr/lib:{env.get('LD_LIBRARY_PATH', '')}"

print("[*] Launching simulation process for local CPU profiling...")
proc = subprocess.Popen(
    ["/usr/bin/python3", str(SIM_SCRIPT)],
    cwd=str(SCRIPTS_DIR),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
pid = proc.pid
print(f"[*] Simulation PID: {pid}")

# Wait for GNU Radio to initialize flowgraph and spawn block threads
time.sleep(4)


def get_thread_names(p):
    names = {}
    for task_dir in glob.glob(f"/proc/{p}/task/*"):
        tid = os.path.basename(task_dir)
        try:
            with open(f"{task_dir}/comm", "r") as f:
                names[tid] = f.read().strip()
        except Exception:
            pass
    return names


thread_names = get_thread_names(pid)
print(f"[*] Discovered {len(thread_names)} active block threads.")

cpu_samples = {}
samples_count = 0
num_iterations = 20

print(f"[*] Profiling across {num_iterations} seconds...")
for i in range(num_iterations):
    if proc.poll() is not None:
        print(f"[*] Process finished early at sample {i+1}.")
        break
    try:
        # Refresh thread names in case new blocks spawned
        current_names = get_thread_names(pid)
        thread_names.update(current_names)

        out = subprocess.check_output(f"ps -T -p {pid} -o spid,%cpu", shell=True, text=True)
        lines = out.strip().split("\n")
        samples_count += 1
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 2:
                tid = parts[0]
                cpu = float(parts[1])
                tname = thread_names.get(tid, f"thread_{tid}")
                cpu_samples[tname] = cpu_samples.get(tname, 0.0) + cpu
    except Exception as e:
        print(f"[-] Warning during sample {i+1}: {e}")
    time.sleep(1)

print("[*] Terminating benchmark process after profiling...")
try:
    proc.terminate()
    proc.wait(timeout=5)
except Exception:
    proc.kill()

if samples_count > 0:
    avg_cpu = {k: round(v / samples_count, 2) for k, v in cpu_samples.items() if v > 0}
    total_cpu = sum(avg_cpu.values())
    perc_cpu = {
        k: round((v / total_cpu) * 100.0, 2)
        for k, v in sorted(avg_cpu.items(), key=lambda x: x[1], reverse=True)
    }

    result = {
        "cpu_model": "Intel(R) Core(TM) i5-1335U",
        "cores_threads": "10 cores (2P + 8E) / 12 threads",
        "avg_cpu_cores": avg_cpu,
        "total_cpu_percent": round(total_cpu, 2),
        "block_percentages": perc_cpu,
        "samples_collected": samples_count
    }

    out_json = SCRIPTS_DIR / "local_block_profile.json"
    with open(out_json, "w") as f:
        json.dump(result, f, indent=4)

    print(f"[+] Profiling complete! Results saved to {out_json}")
    print(f"    Total CPU observed: {total_cpu:.2f}%")
    print(f"    Top 5 consuming blocks:")
    top5 = list(perc_cpu.items())[:5]
    for b, p in top5:
        print(f"      - {b}: {p}% ({avg_cpu.get(b, 0)}% of a core)")
else:
    print("[-] Error: No samples collected.")
