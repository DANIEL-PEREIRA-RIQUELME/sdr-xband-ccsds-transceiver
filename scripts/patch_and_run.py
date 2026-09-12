import sys
import os
import subprocess
import time
import re

base_script = "../flowgraphs/RS_CC_TX_RCV.py"
with open(base_script, "r") as f:
    code = f.read()

# Inject msg catcher
injection = """
class MsgCatcher(gr.sync_block):
    def __init__(self, filename):
        gr.sync_block.__init__(self, "msg_catcher", in_sig=None, out_sig=None)
        self.message_port_register_in(pmt.intern("freq"))
        self.set_msg_handler(pmt.intern("freq"), self.handle_msg)
        self.filename = filename
        with open(self.filename, 'w') as f:
            f.write("[]")
        self.freqs = []
        import threading
        self.t = threading.Thread(target=self.dumper)
        self.t.daemon = True
        self.t.start()
    def handle_msg(self, msg):
        if pmt.is_pair(msg):
            key = pmt.symbol_to_string(pmt.car(msg))
            if key == "freq_hz":
                val = pmt.to_double(pmt.cdr(msg))
                self.freqs.append(val)
    def dumper(self):
        import time, json
        while True:
            time.sleep(2)
            with open(self.filename, 'w') as f:
                json.dump(self.freqs, f)

"""

code = code.replace("class RS_CC_TX_RCV(gr.top_block):", injection + "\nclass RS_CC_TX_RCV(gr.top_block):")

# Find the block connections
connection_code = "self.connect((self.chess_downlink_channel_0, 0), (self.chess_coarse_doppler_sync_0, 0))"
patched_conn = connection_code + """
        self.msg_catcher_0 = MsgCatcher(f"../output/results/test/freqs_{self.ebn0_db}.json")
        self.msg_connect((self.chess_coarse_doppler_sync_0, "freq"), (self.msg_catcher_0, "freq"))
"""
code = code.replace(connection_code, patched_conn)


ebn0_values = [2.0, 2.8, 3.6, 4.4, 5.2, 6.0]

for ebn0 in ebn0_values:
    print(f"=== Running simulation for Eb/N0 = {ebn0} ===")
    current_code = code
    current_code = re.sub(r'self\.ebn0_db = ebn0_db = .*', f'self.ebn0_db = ebn0_db = {ebn0}', current_code)
    current_code = re.sub(r"'output/samples/test/output_2m_.*'", f"'../output/samples/test/output_2m_{ebn0}'", current_code)
    current_code = current_code.replace("'data/test_signal_0.06Ms_CCSDS_I_8'", "'../data/test_signal_0.06Ms_CCSDS_I_8'")
    current_code = current_code.replace("'data/32bitASM_CCSDS_only'", "'../data/32bitASM_CCSDS_only'")
    
    with open("temp_runner.py", "w") as f:
        f.write(current_code)
        
    env = os.environ.copy()
    env["GR_CONF_CONTROLPORT_ON"] = "True"
    env["GR_CONF_PERFCOUNTERS_EXPORT"] = "True"
    
    proc = subprocess.Popen(["/usr/bin/python3", "temp_runner.py"], env=env)
    
    # Run for 20 seconds
    if ebn0 == 6.0:
        time.sleep(10)
        print("Starting dump_performance.py...")
        subprocess.run(["/usr/bin/python3", "dump_performance.py"])
        time.sleep(10)
    else:
        time.sleep(20)
        
    proc.kill()
    proc.wait()
    
    # Move unneeded files
    for f in os.listdir("../output/samples/test/"):
        if f != f"output_2m_{ebn0}":
            os.remove(f"../output/samples/test/{f}")

    # run diagnostic
    subprocess.run(["./diagnostic"])
    import shutil
    try:
        shutil.copy(f"../output/results/test/diagnostic_results_{ebn0}.txt", f"../output/results/test/diagnostic_{ebn0}.txt")
    except:
        pass

print("All simulations finished.")
