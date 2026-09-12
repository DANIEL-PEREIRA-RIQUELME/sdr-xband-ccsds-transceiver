#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: CCSDS X-Band Satellite Transceiver (QPSK + RS/CC, I=8)
# GNU Radio version: 3.10.12.0

import os
import sys
import logging as log

def get_state_directory() -> str:
    oldpath = os.path.expanduser("~/.grc_gnuradio")
    try:
        from gnuradio.gr import paths
        newpath = paths.persistent()
        if os.path.exists(newpath):
            return newpath
        if os.path.exists(oldpath):
            log.warning(f"Found persistent state path '{newpath}', but file does not exist. " +
                     f"Old default persistent state path '{oldpath}' exists; using that. " +
                     "Please consider moving state to new location.")
            return oldpath
        # Default to the correct path if both are configured.
        # neither old, nor new path exist: create new path, return that
        os.makedirs(newpath, exist_ok=True)
        return newpath
    except (ImportError, NameError):
        log.warning("Could not retrieve GNU Radio persistent state directory from GNU Radio. " +
                 "Trying defaults.")
        xdgstate = os.getenv("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
        xdgcand = os.path.join(xdgstate, "gnuradio")
        if os.path.exists(xdgcand):
            return xdgcand
        if os.path.exists(oldpath):
            log.warning(f"Using legacy state path '{oldpath}'. Please consider moving state " +
                     f"files to '{xdgcand}'.")
            return oldpath
        # neither old, nor new path exist: create new path, return that
        os.makedirs(xdgcand, exist_ok=True)
        return xdgcand

sys.path.append(os.environ.get('GRC_HIER_PATH', get_state_directory()))

from ccsds_concatenated_rx import ccsds_concatenated_rx  # grc-generated hier_block
from ccsds_concatenated_tx import ccsds_concatenated_tx  # grc-generated hier_block
from gnuradio import blocks
import pmt
from gnuradio import chess
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import math
import threading




class RS_CC_TX_RCV(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "CCSDS X-Band Satellite Transceiver (QPSK + RS/CC, I=8)", catch_exceptions=True)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 2
        self.samp_rate = samp_rate = 25000000
        self.rolloff = rolloff = 0.5
        self.f_tx = f_tx = 8.4e9
        self.ebn0_db = ebn0_db = 3
        self.altitude = altitude = 475.0

        ##################################################
        # Blocks
        ##################################################

        self.chess_downlink_channel_0 = chess.downlink_channel(samp_rate, 8.4e9, 475, 90.0, 53.0, math.sqrt(sps / (10**(ebn0_db / 10.0) * (223.0/259.0))), -150.0)
        self.chess_coarse_doppler_sync_0 = chess.coarse_doppler_sync(samp_rate, 16384, 131072, 4, True, 0.7, 1.0, 8)
        self.ccsds_concatenated_tx_0 = ccsds_concatenated_tx(
            interleave=8,
            rolloff=0.5,
            samp_rate=25000000,
            sps=2,
        )
        self.ccsds_concatenated_rx_0 = ccsds_concatenated_rx(
            interleave=8,
            loop_bw=0.002,
            max_missed=1,
            rolloff=0.5,
            samp_rate=25000000,
            sps=2,
            sync_threshold=0,
        )
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex*1)
        self.blocks_file_source_0_0_0_0_0_0 = blocks.file_source(gr.sizeof_char*1, 'data/test_signal_0.06Ms_CCSDS_I_8', False, 0, 0)
        self.blocks_file_source_0_0_0_0_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_0_0_0_0_0.set_processor_affinity([1])
        self.blocks_file_source_0_0_0_0_0 = blocks.file_source(gr.sizeof_char*1, 'data/32bitASM_CCSDS_only', True, 0, 0)
        self.blocks_file_source_0_0_0_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_0_0_0_0.set_processor_affinity([1])
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, 'output/samples/test/output_2m_3_50', False)
        self.blocks_file_sink_0.set_unbuffered(True)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0_0_0_0_0, 0), (self.ccsds_concatenated_tx_0, 1))
        self.connect((self.blocks_file_source_0_0_0_0_0_0, 0), (self.ccsds_concatenated_tx_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.chess_downlink_channel_0, 0))
        self.connect((self.ccsds_concatenated_rx_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.ccsds_concatenated_rx_0, 1), (self.blocks_null_sink_0, 0))
        self.connect((self.ccsds_concatenated_tx_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.chess_coarse_doppler_sync_0, 0), (self.ccsds_concatenated_rx_0, 0))
        self.connect((self.chess_downlink_channel_0, 0), (self.chess_coarse_doppler_sync_0, 0))


    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)

    def get_rolloff(self):
        return self.rolloff

    def set_rolloff(self, rolloff):
        self.rolloff = rolloff

    def get_f_tx(self):
        return self.f_tx

    def set_f_tx(self, f_tx):
        self.f_tx = f_tx

    def get_ebn0_db(self):
        return self.ebn0_db

    def set_ebn0_db(self, ebn0_db):
        self.ebn0_db = ebn0_db

    def get_altitude(self):
        return self.altitude

    def set_altitude(self, altitude):
        self.altitude = altitude




def main(top_block_cls=RS_CC_TX_RCV, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    tb.flowgraph_started.set()

    tb.wait()


if __name__ == '__main__':
    main()
