#include <iostream>
#include <fstream>
#include <vector>
#include <cstdint>
#include <bit>       // Para std::popcount (C++20)
#include <algorithm>
#include <iomanip>
#include <string>
#include <filesystem>

namespace fs = std::filesystem;

//! Cambiar la linea 206 si cambia el nombre de los archivos
// --- Parameters ---
const size_t FRAME_SIZE = 1784; // Cambiar a 223 para I=1, o 1115 para I=5
const size_t WARMUP_FRAMES = 0;
const size_t TAIL_FRAMES = 10;
const size_t ALIGN_WINDOW = 100;

// CRC-16-CCITT calculation
uint16_t crc16_ccitt(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; ++i) {
        crc ^= (data[i] << 8);
        for (int j = 0; j < 8; ++j) {
            crc = (crc & 0x8000) ? ((crc << 1) ^ 0x1021) : (crc << 1);
        }
    }
    return crc;
}

// Hardware-accelerated bit error counting
int count_bit_errors(const uint8_t* a, const uint8_t* b, size_t length) {
    int errors = 0;
    for (size_t i = 0; i < length; ++i) {
        unsigned int val = static_cast<unsigned int>(a[i] ^ b[i]);
        errors += std::popcount(val);
    }
    return errors;
}

// Fast byte-level error counting for alignment
int count_byte_errors(const uint8_t* a, const uint8_t* b, size_t length) {
    int errors = 0;
    for (size_t i = 0; i < length; ++i) {
        if (a[i] != b[i]) errors++;
    }
    return errors;
}

void run_diagnostic(const std::string& rx_file, const std::string& result_file, const std::vector<uint8_t>& tx_data) {
    size_t num_tx_frames = tx_data.size() / FRAME_SIZE;

    // Load RX file robustly
    std::ifstream rx_stream(rx_file, std::ios::binary | std::ios::ate);
    if (!rx_stream) {
        std::cerr << "File Error: Could not open " << rx_file << std::endl;
        return;
    }
    size_t rx_size = rx_stream.tellg();
    rx_stream.seekg(0, std::ios::beg);
    
    size_t num_rx_frames = rx_size / FRAME_SIZE;
    std::vector<uint8_t> rx_data(num_rx_frames * FRAME_SIZE);
    
    // Leer y comprobar
    rx_stream.read(reinterpret_cast<char*>(rx_data.data()), rx_data.size());
    size_t bytes_read = rx_stream.gcount();
    if (bytes_read != rx_data.size()) {
        std::cerr << "Warning: Read " << bytes_read << " bytes instead of " << rx_data.size() << std::endl;
        rx_data.resize(bytes_read);
        num_rx_frames = bytes_read / FRAME_SIZE;
    }

    std::ofstream out(result_file);
    out << "--- CCSDS DETAILED FRAME LOG ---\n";
    out << std::left << std::setw(10) << "FrameIdx" << " | "
        << std::setw(10) << "Status" << " | "
        << std::setw(10) << "BitErrors" << " | CRC\n";
    out << std::string(50, '-') << "\n";
    
    size_t expected_seq = 0;
    
    // Protecciones de límites
    size_t eval_end_idx = (num_tx_frames > TAIL_FRAMES) ? (num_tx_frames - TAIL_FRAMES) : 0;
    size_t total_eval_frames = (eval_end_idx > WARMUP_FRAMES) ? (eval_end_idx - WARMUP_FRAMES) : 0;
    
    // Variables de tracking (alineadas con lógica Python)
    size_t valid_frames_count = 0;
    size_t crc_fails_count = 0;
    uint64_t sync_bit_errors = 0;

    for (size_t rx_idx = 0; rx_idx < num_rx_frames; ++rx_idx) {
        if (expected_seq >= num_tx_frames) break;

        const uint8_t* current_rx_frame = &rx_data[rx_idx * FRAME_SIZE];
        size_t max_search = std::min(expected_seq + ALIGN_WINDOW, num_tx_frames);
        
        size_t best_match_idx = expected_seq;
        int min_byte_err = FRAME_SIZE + 1;

        // Búsqueda rápida
        for (size_t search_idx = expected_seq; search_idx < max_search; ++search_idx) {
            const uint8_t* current_tx_frame = &tx_data[search_idx * FRAME_SIZE];
            int err = count_byte_errors(current_tx_frame, current_rx_frame, FRAME_SIZE);
            if (err < min_byte_err) {
                min_byte_err = err;
                best_match_idx = search_idx;
            }
        }

        // Cuenta de bits reales
        int min_bit_err = count_bit_errors(&tx_data[best_match_idx * FRAME_SIZE], current_rx_frame, FRAME_SIZE);

        // Umbral de basura
        int error_threshold = static_cast<int>(FRAME_SIZE * 8 * 0.25);
        if (min_bit_err > error_threshold) continue; 

        // Comprobación de CRC
        uint16_t received_crc = (current_rx_frame[FRAME_SIZE - 2] << 8) | current_rx_frame[FRAME_SIZE - 1];
        bool crc_pass = (crc16_ccitt(current_rx_frame, FRAME_SIZE - 2) == received_crc);

        // Evaluamos si cae en la ventana
        if (best_match_idx >= WARMUP_FRAMES && best_match_idx < eval_end_idx) {
            if (crc_pass) {
                valid_frames_count++;
                sync_bit_errors += min_bit_err; // Solo sumamos bits de tramas VÁLIDAS
            } else {
                crc_fails_count++;
            }

            size_t frames_lost = best_match_idx - expected_seq;
            if (frames_lost > 0) {
                out << "\n!!! LOST " << frames_lost << " FRAMES BEFORE INDEX " << best_match_idx << " !!!\n";
            }
            if (min_bit_err > 0 || !crc_pass) {
                out << std::left << std::setw(10) << best_match_idx << " | " 
                    << std::setw(10) << (min_bit_err > 0 ? "CORRUPT" : "OK") << " | "
                    << std::setw(10) << min_bit_err << " | " 
                    << (crc_pass ? "PASS" : "FAIL") << "\n";
            }
        }
        expected_seq = best_match_idx + 1;
    }

    // --- FINAL METRICS CALCULATION (ESPEJO DE PYTHON) ---
    size_t matched_frames = valid_frames_count + crc_fails_count;
    size_t sync_lost_frames = (total_eval_frames > matched_frames) ? (total_eval_frames - matched_frames) : 0;
    
    // Total tramas inútiles (perdidas + CRC fallado)
    size_t total_useless_frames = sync_lost_frames + crc_fails_count;
    double fer = total_eval_frames > 0 ? static_cast<double>(total_useless_frames) / total_eval_frames : 0.0;
    
    // SYNC BER (Solo de tramas VÁLIDAS)
    uint64_t sync_total_bits = static_cast<uint64_t>(valid_frames_count) * FRAME_SIZE * 8;
    double sync_ber = sync_total_bits > 0 ? static_cast<double>(sync_bit_errors) / sync_total_bits : 0.0;
    
    // SYSTEM BER (Añade penalización del 50% a TODAS las tramas inútiles)
    uint64_t system_total_bits = static_cast<uint64_t>(total_eval_frames) * FRAME_SIZE * 8;
    uint64_t penalty_errors = static_cast<uint64_t>(total_useless_frames * FRAME_SIZE * 8 * 0.5);
    uint64_t total_system_errors = sync_bit_errors + penalty_errors;
    double system_ber = total_eval_frames > 0 ? static_cast<double>(total_system_errors) / system_total_bits : 1.0;

    out << "\n========================================\n"
        << "             FINAL SUMMARY\n"
        << "========================================\n"
        << "=== FRAME METRICS ===\n"
        << "Total Frames Evaluated : " << total_eval_frames << "\n"
        << "Frames Rx (Valid CRC)  : " << valid_frames_count << " (" 
        << std::fixed << std::setprecision(2) << (total_eval_frames > 0 ? ((double)valid_frames_count/total_eval_frames)*100.0 : 0.0) << "%)\n"
        << "Frames Lost (Sync Fail): " << sync_lost_frames << "\n"
        << "Frames Rx (CRC Fail)   : " << crc_fails_count << "\n"
        << "Frame Error Rate (FER) : " << std::scientific << std::setprecision(4) << fer << "\n\n"
        << "=== BIT ERROR RATES (BER) ===\n"
        << "Sync BER (Valid only)  : " << std::scientific << sync_ber << "  <- Errors inside successfully received frames\n"
        << "Global System BER      : " << std::scientific << system_ber << "  <- Includes 50% error penalty for all useless frames\n"
        << "========================================\n";

    std::cout << "Saved: " << result_file << " | FER: " << std::scientific << fer << " | Sys BER: " << system_ber << std::endl;
}

std::string find_project_root() {
    const std::vector<std::string> candidates = {
        "../",
        "./",
        "../../",
        "/home/dan/Documents/PROJECTS/X-band TFG/"
    };
    for (const auto& dir : candidates) {
        if (fs::exists(dir + "data") || fs::exists(dir + "files")) {
            return dir;
        }
    }
    return "../";
}

int main(int argc, char* argv[]) {
    std::string root = find_project_root();
    
    std::string TX_FILE = fs::exists(root + "data/test_signal_1Ms_CCSDS_I_8") 
                        ? (root + "data/test_signal_1Ms_CCSDS_I_8")
                        : (root + "files/test_signal_1Ms_CCSDS_I_8");
                        
    std::string SAMPLES_DIR = fs::exists(root + "output/samples/test/")
                            ? (root + "output/samples/test/")
                            : (root + "samples/test/");
                            
    std::string RESULT_DIR = fs::exists(root + "output/results/test/")
                           ? (root + "output/results/test/")
                           : (root + "results/test/");

    if (!fs::exists(SAMPLES_DIR)) {
        std::cerr << "Error: Samples directory not found at " << SAMPLES_DIR << std::endl;
        return 1;
    }

    fs::create_directories(RESULT_DIR);

    std::cout << "Loading Reference TX file into memory (" << TX_FILE << ")..." << std::endl;
    std::ifstream tx_stream(TX_FILE, std::ios::binary | std::ios::ate);
    if (!tx_stream) {
        std::cerr << "Error: Could not open TX file at " << TX_FILE << "!" << std::endl;
        return 1;
    }
    size_t tx_size = tx_stream.tellg();
    tx_stream.seekg(0, std::ios::beg);
    std::vector<uint8_t> tx_data(tx_size);
    tx_stream.read(reinterpret_cast<char*>(tx_data.data()), tx_size);

    std::vector<std::string> rx_files;
    if (argc > 1) {
        std::string arg = argv[1];
        if (fs::exists(arg)) {
            rx_files.push_back(arg);
        } else if (fs::exists(SAMPLES_DIR + arg)) {
            rx_files.push_back(SAMPLES_DIR + arg);
        } else {
            std::cerr << "Error: Specified file " << arg << " not found!" << std::endl;
            return 1;
        }
    } else {
        for (const auto& entry : fs::directory_iterator(SAMPLES_DIR)) {
            std::string filename = entry.path().filename().string();
            // Busca prefijo "output_2m_"
            if (filename.find("output_2m_") == 0) {
                rx_files.push_back(filename);
            }
        }
        if (rx_files.empty()) {
            for (const auto& entry : fs::directory_iterator(SAMPLES_DIR)) {
                std::string filename = entry.path().filename().string();
                if (filename.find("output_") == 0) {
                    rx_files.push_back(filename);
                }
            }
        }
    }

    std::sort(rx_files.begin(), rx_files.end());

    std::cout << "--- Starting automated processing of " << rx_files.size() << " files ---\n";

    for (const auto& file_entry : rx_files) {
        std::string filename = fs::path(file_entry).filename().string();
        std::cout << ">> Processing: " << filename << "... ";
        
        std::string snr_value;
        if (filename.find("output_2m_") == 0) {
            snr_value = filename.substr(10);
        } else if (filename.find("output_") == 0) {
            snr_value = filename.substr(7);
        } else {
            snr_value = filename;
        }
        std::replace(snr_value.begin(), snr_value.end(), '_', '.');

        std::string rx_path = fs::exists(file_entry) ? file_entry : (SAMPLES_DIR + filename);
        std::string result_path = RESULT_DIR + "diagnostic_results_" + snr_value + ".txt";

        run_diagnostic(rx_path, result_path, tx_data);
    }

    std::cout << "=== BATCH PROCESSING FINISHED ===\n";
    return 0;
}