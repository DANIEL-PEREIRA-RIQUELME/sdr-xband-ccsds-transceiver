#!/usr/bin/env python3
"""
GNU Radio ControlPort Performance Metrics Collector
===================================================
Connects via Apache Thrift to GNU Radio ControlPort on port 9090,
samples block-level work time and CPU metrics, and exports averaged JSON reports.

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""

import sys
import json
import time

# Ensure system ControlPort libraries can be imported
sys.path.insert(0, '/usr/lib/python3/dist-packages')

try:
    from gnuradio.ctrlport.GNURadioControlPortClient import GNURadioControlPortClient
except ImportError:
    print("[-] Error: GNU Radio ControlPort client library not found.")
    sys.exit(1)


def fetch_and_save(client):
    print("[*] Connected to ControlPort. Collecting performance metrics across 10 seconds...")
    
    samples_collected = 0
    accumulated_data = {}
    
    for i in range(10):
        print(f"    -> Sample {i+1}/10...")
        knobs = client.getKnobs('')
        
        for key, value in knobs.items():
            if "work time" in key or "cpu" in key.lower():
                block_name = key.split('::')[0]
                metric_name = key.split('::')[-1]
                
                if block_name not in accumulated_data:
                    accumulated_data[block_name] = {}
                
                if metric_name not in accumulated_data[block_name]:
                    accumulated_data[block_name][metric_name] = 0.0
                
                accumulated_data[block_name][metric_name] += float(value.value)
                
        samples_collected += 1
        time.sleep(1)
        
    final_data = {}
    for block_name, metrics in accumulated_data.items():
        final_data[block_name] = {}
        for metric_name, total_val in metrics.items():
            final_data[block_name][metric_name] = total_val / samples_collected

    filename = "perf_metrics_average_10s.json"
    with open(filename, 'w') as f:
        json.dump(final_data, f, indent=4)
        
    print(f"[+] Success! Averaged performance metrics saved to: {filename}")
    print("[*] Metrics ready for downstream profiling or visualization.")
    sys.exit(0)


if __name__ == '__main__':
    print("[*] Attempting to connect to ControlPort on 127.0.0.1:9090...")
    client = GNURadioControlPortClient(host='127.0.0.1', port=9090, rpcmethod='thrift', callback=fetch_and_save)
