#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.12.0

import os
import sys
user_pkg = os.path.expanduser('~/.local/lib/python3.12/dist-packages')
if user_pkg not in sys.path:
    sys.path.insert(0, user_pkg)

from gnuradio import analog
from gnuradio import blocks
import pmt
from gnuradio import chess
from gnuradio import digital
from gnuradio import fec
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, pdu
import math
import satellites
import threading




class RS_CC_TX_RCV(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.variable_cc_encoder_def_0 = variable_cc_encoder_def_0 = fec.cc_encoder_make(16352,7, 2, [79,-109], 0, fec.CC_STREAMING, False)
        self.variable_cc_decoder_def_1 = variable_cc_decoder_def_1 = fec.cc_decoder.make(16352,7, 2, [79,-109], 0, (-1), fec.CC_STREAMING, False)
        self.variable_cc_decoder_def_0 = variable_cc_decoder_def_0 = fec.cc_decoder.make(16352,7, 2, [79,-109], 0, (-1), fec.CC_STREAMING, False)
        self.sps = sps = 2
        self.samp_rate = samp_rate = 25000000
        self.rolloff = rolloff = 0.5
        self.f_tx = f_tx = 8.4e9
        self.ebn0_db = ebn0_db = 3
        self.constel = constel = digital.constellation_calcdist(digital.psk_4()[0], digital.psk_4()[1],
        4, 1, digital.constellation.AMPLITUDE_NORMALIZATION).base()
        self.constel.set_npwr(1.0)
        self.constel.gen_soft_dec_lut(8)
        self.altitude = altitude = 475.0

        ##################################################
        # Blocks
        ##################################################

        self.satellites_decode_rs_ccsds_0 = satellites.decode_rs(True, 8)
        self.root_raised_cosine_filter_0_0_0 = filter.interp_fir_filter_ccf(
            2,
            firdes.root_raised_cosine(
                sps,
                samp_rate,
                (samp_rate/sps),
                rolloff,
                32))
        self.pdu_tagged_stream_to_pdu_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.fec_extended_encoder_0 = fec.extended_encoder(encoder_obj_list=variable_cc_encoder_def_0, threading='capillary', puncpat='11')
        self.fec_extended_decoder_0_1 = fec.extended_decoder(decoder_obj_list=variable_cc_decoder_def_1, threading='capillary', ann=None, puncpat='11', integration_period=10000)
        self.fec_extended_decoder_0 = fec.extended_decoder(decoder_obj_list=variable_cc_decoder_def_0, threading='capillary', ann=None, puncpat='11', integration_period=10000)
        self.digital_pfb_clock_sync_xxx_0_0 = digital.pfb_clock_sync_ccf(2, 0.005, firdes.root_raised_cosine(32,64,1.0,0.5,1704), 32, 0, 1.5, 1)
        self.digital_costas_loop_cc_0_0 = digital.costas_loop_cc(0.002, 4, False)
        self.digital_constellation_soft_decoder_cf_0_0_1 = digital.constellation_soft_decoder_cf(constel, -1)
        self.digital_constellation_soft_decoder_cf_0_0 = digital.constellation_soft_decoder_cf(constel, -1)
        self.digital_chunks_to_symbols_xx_0 = digital.chunks_to_symbols_bc(constel.points(), 1)
        self.chess_encode_rs_1 = chess.encode_rs(1784, True, 8)
        self.chess_dual_branch_flywheel_sync_0 = chess.fast_sync("1ACFFC1D", "E53003E2", 16320, 0, 1)
        self.chess_doppler_channel_0 = chess.doppler_channel(samp_rate, 10.475e9, 475.0, 90.0, 53.0, 478.0, 91, 52.5, math.sqrt(sps / (10**(ebn0_db / 10.0) * (223.0/259.0))))
        self.chess_ccsds_scrambler_tx_0 = chess.ccsds_scrambler_tx()
        self.chess_ccsds_descrambler_rx_1 = chess.ccsds_descrambler_rx()
        self.blocks_vector_to_stream_0_1 = blocks.vector_to_stream(gr.sizeof_char*1, 2040)
        self.blocks_unpack_k_bits_bb_0_0_0_0_0 = blocks.unpack_k_bits_bb(8)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_tag_gate_0_0 = blocks.tag_gate(gr.sizeof_char * 1, False)
        self.blocks_tag_gate_0_0.set_single_key("")
        self.blocks_tag_gate_0 = blocks.tag_gate(gr.sizeof_char * 1, False)
        self.blocks_tag_gate_0.set_single_key("")
        self.blocks_stream_to_vector_2_0 = blocks.stream_to_vector(gr.sizeof_char*1, 1784)
        self.blocks_stream_to_tagged_stream_0_0_1 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 16320, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 1784, "packet_len")
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 2040, "packet_len")
        self.blocks_stream_mux_0 = blocks.stream_mux(gr.sizeof_char*1, (32, 16320))
        self.blocks_repack_bits_bb_0 = blocks.repack_bits_bb(8, 2, "", False, gr.GR_MSB_FIRST)
        self.blocks_pack_k_bits_bb_0_0 = blocks.pack_k_bits_bb(8)
        self.blocks_pack_k_bits_bb_0 = blocks.pack_k_bits_bb(8)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_char*1)
        self.blocks_multiply_const_vxx_1 = blocks.multiply_const_cc(1j)
        self.blocks_file_source_0_0_0_0_0_0 = blocks.file_source(gr.sizeof_char*1, 'data/test_signal_0.06Ms_CCSDS_I_8', False, 0, 0)
        self.blocks_file_source_0_0_0_0_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_0_0_0_0_0.set_processor_affinity([1])
        self.blocks_file_source_0_0_0_0_0 = blocks.file_source(gr.sizeof_char*1, 'data/32bitASM_CCSDS_only', True, 0, 0)
        self.blocks_file_source_0_0_0_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_0_0_0_0.set_processor_affinity([1])
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, 'samples/test/output_2m_3_50', False)
        self.blocks_file_sink_0.set_unbuffered(True)
        self.analog_agc_xx_0 = analog.agc_cc((1e-4), 1.0, 1.0, 65536)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0, 'pdus'), (self.satellites_decode_rs_ccsds_0, 'in'))
        self.msg_connect((self.satellites_decode_rs_ccsds_0, 'out'), (self.pdu_pdu_to_tagged_stream_0_0, 'pdus'))
        self.connect((self.analog_agc_xx_0, 0), (self.digital_pfb_clock_sync_xxx_0_0, 0))
        self.connect((self.blocks_file_source_0_0_0_0_0, 0), (self.blocks_stream_mux_0, 0))
        self.connect((self.blocks_file_source_0_0_0_0_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.digital_constellation_soft_decoder_cf_0_0_1, 0))
        self.connect((self.blocks_pack_k_bits_bb_0, 0), (self.blocks_repack_bits_bb_0, 0))
        self.connect((self.blocks_pack_k_bits_bb_0_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.digital_chunks_to_symbols_xx_0, 0))
        self.connect((self.blocks_stream_mux_0, 0), (self.fec_extended_encoder_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.pdu_tagged_stream_to_pdu_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0, 0), (self.blocks_stream_to_vector_2_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_1, 0), (self.chess_ccsds_scrambler_tx_0, 0))
        self.connect((self.blocks_stream_to_vector_2_0, 0), (self.chess_encode_rs_1, 0))
        self.connect((self.blocks_tag_gate_0, 0), (self.chess_dual_branch_flywheel_sync_0, 0))
        self.connect((self.blocks_tag_gate_0_0, 0), (self.chess_dual_branch_flywheel_sync_0, 1))
        self.connect((self.blocks_throttle2_0, 0), (self.chess_doppler_channel_0, 0))
        self.connect((self.blocks_unpack_k_bits_bb_0_0_0_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_1, 0))
        self.connect((self.blocks_vector_to_stream_0_1, 0), (self.blocks_unpack_k_bits_bb_0_0_0_0_0, 0))
        self.connect((self.chess_ccsds_descrambler_rx_1, 0), (self.blocks_pack_k_bits_bb_0_0, 0))
        self.connect((self.chess_ccsds_scrambler_tx_0, 0), (self.blocks_stream_mux_0, 1))
        self.connect((self.chess_doppler_channel_0, 0), (self.analog_agc_xx_0, 0))
        self.connect((self.chess_dual_branch_flywheel_sync_0, 0), (self.chess_ccsds_descrambler_rx_1, 0))
        self.connect((self.chess_encode_rs_1, 0), (self.blocks_vector_to_stream_0_1, 0))
        self.connect((self.digital_chunks_to_symbols_xx_0, 0), (self.root_raised_cosine_filter_0_0_0, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_0_0, 0), (self.fec_extended_decoder_0, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_0_0_1, 0), (self.fec_extended_decoder_0_1, 0))
        self.connect((self.digital_costas_loop_cc_0_0, 0), (self.blocks_multiply_const_vxx_1, 0))
        self.connect((self.digital_costas_loop_cc_0_0, 0), (self.digital_constellation_soft_decoder_cf_0_0, 0))
        self.connect((self.digital_pfb_clock_sync_xxx_0_0, 0), (self.digital_costas_loop_cc_0_0, 0))
        self.connect((self.fec_extended_decoder_0, 0), (self.blocks_tag_gate_0, 0))
        self.connect((self.fec_extended_decoder_0_1, 0), (self.blocks_tag_gate_0_0, 0))
        self.connect((self.fec_extended_encoder_0, 0), (self.blocks_pack_k_bits_bb_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.root_raised_cosine_filter_0_0_0, 0), (self.blocks_throttle2_0, 0))


    def get_variable_cc_encoder_def_0(self):
        return self.variable_cc_encoder_def_0

    def set_variable_cc_encoder_def_0(self, variable_cc_encoder_def_0):
        self.variable_cc_encoder_def_0 = variable_cc_encoder_def_0

    def get_variable_cc_decoder_def_1(self):
        return self.variable_cc_decoder_def_1

    def set_variable_cc_decoder_def_1(self, variable_cc_decoder_def_1):
        self.variable_cc_decoder_def_1 = variable_cc_decoder_def_1

    def get_variable_cc_decoder_def_0(self):
        return self.variable_cc_decoder_def_0

    def set_variable_cc_decoder_def_0(self, variable_cc_decoder_def_0):
        self.variable_cc_decoder_def_0 = variable_cc_decoder_def_0

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.root_raised_cosine_filter_0_0_0.set_taps(firdes.root_raised_cosine(self.sps, self.samp_rate, (self.samp_rate/self.sps), self.rolloff, 32))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.root_raised_cosine_filter_0_0_0.set_taps(firdes.root_raised_cosine(self.sps, self.samp_rate, (self.samp_rate/self.sps), self.rolloff, 32))

    def get_rolloff(self):
        return self.rolloff

    def set_rolloff(self, rolloff):
        self.rolloff = rolloff
        self.root_raised_cosine_filter_0_0_0.set_taps(firdes.root_raised_cosine(self.sps, self.samp_rate, (self.samp_rate/self.sps), self.rolloff, 32))

    def get_f_tx(self):
        return self.f_tx

    def set_f_tx(self, f_tx):
        self.f_tx = f_tx

    def get_ebn0_db(self):
        return self.ebn0_db

    def set_ebn0_db(self, ebn0_db):
        self.ebn0_db = ebn0_db

    def get_constel(self):
        return self.constel

    def set_constel(self, constel):
        self.constel = constel
        self.digital_constellation_soft_decoder_cf_0_0.set_constellation(self.constel)
        self.digital_constellation_soft_decoder_cf_0_0_1.set_constellation(self.constel)

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
