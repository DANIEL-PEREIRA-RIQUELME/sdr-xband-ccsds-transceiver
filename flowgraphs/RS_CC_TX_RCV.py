#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: CCSDS X-Band Satellite Transceiver (QPSK + RS/CC, I=8)
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
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
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import math
import sip
import threading



class RS_CC_TX_RCV(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "CCSDS X-Band Satellite Transceiver (QPSK + RS/CC, I=8)", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("CCSDS X-Band Satellite Transceiver (QPSK + RS/CC, I=8)")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "RS_CC_TX_RCV")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 2
        self.samp_rate = samp_rate = 25000000
        self.rolloff = rolloff = 0.5
        self.f_tx = f_tx = 8.4e9
        self.ebn0_db = ebn0_db = 14
        self.altitude = altitude = 475.0

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            1024, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(False)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_0_win)
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
            loop_bw=0.001,
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
        self.connect((self.ccsds_concatenated_rx_0, 1), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.ccsds_concatenated_tx_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.chess_coarse_doppler_sync_0, 0), (self.ccsds_concatenated_rx_0, 0))
        self.connect((self.chess_downlink_channel_0, 0), (self.chess_coarse_doppler_sync_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "RS_CC_TX_RCV")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

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

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
