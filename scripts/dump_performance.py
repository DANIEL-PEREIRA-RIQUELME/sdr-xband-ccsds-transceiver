#!/usr/bin/python3
import sys
import json
import time

# Necesario para cargar las librerías de ControlPort
sys.path.insert(0, '/usr/lib/python3/dist-packages')

try:
    from gnuradio.ctrlport.GNURadioControlPortClient import GNURadioControlPortClient
except ImportError:
    print("Error: No se encuentra la librería de ControlPort.")
    sys.exit(1)

def fetch_and_save(client):
    print("[*] Conectado a ControlPort. Recopilando métricas durante 10 segundos...")
    
    samples_collected = 0
    accumulated_data = {}
    
    # Recopilar durante 10 segundos (10 iteraciones, 1 por segundo)
    for i in range(10):
        print(f"    -> Muestra {i+1}/10...")
        knobs = client.getKnobs('')
        
        for key, value in knobs.items():
            if "work time" in key or "cpu" in key.lower():
                block_name = key.split('::')[0]
                metric_name = key.split('::')[-1]
                
                if block_name not in accumulated_data:
                    accumulated_data[block_name] = {}
                
                if metric_name not in accumulated_data[block_name]:
                    accumulated_data[block_name][metric_name] = 0.0
                
                # Sumarizamos el valor (asumimos numérico)
                accumulated_data[block_name][metric_name] += float(value.value)
                
        samples_collected += 1
        time.sleep(1)
        
    # Calcular promedios
    final_data = {}
    for block_name, metrics in accumulated_data.items():
        final_data[block_name] = {}
        for metric_name, total_val in metrics.items():
            final_data[block_name][metric_name] = total_val / samples_collected

    # Guardar en JSON
    filename = f"perf_metrics_promedio_10s.json"
    with open(filename, 'w') as f:
        json.dump(final_data, f, indent=4)
        
    print(f"[+] ¡Éxito! Métricas promediadas guardadas en: {filename}")
    print("[*] Ahora puedes cargar este JSON en Pandas, Excel, o tu script de análisis.")
    
    # Salimos
    sys.exit(0)

if __name__ == '__main__':
    print("[*] Intentando conectar al puerto 9090...")
    # Creamos el cliente apuntando al localhost y nuestro puerto
    client = GNURadioControlPortClient(host='127.0.0.1', port=9090, rpcmethod='thrift', callback=fetch_and_save)
