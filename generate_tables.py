import numpy as np

def hz_to_mel(hz):
    return 2595.0 * np.log10(1.0 + hz / 700.0)

def mel_to_hz(mel):
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

def get_mel_filterbank(n_filters=40, n_fft=512, sr=16000, low_f=80, high_f=7600):
    low_mel = hz_to_mel(low_f)
    high_mel = hz_to_mel(high_f)
    mel_points = np.linspace(low_mel, high_mel, n_filters + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = np.floor((n_fft + 1) * hz_points / sr).astype(int)

    fbank = np.zeros((n_filters, int(np.floor(n_fft / 2 + 1))))
    for m in range(1, n_filters + 1):
        f_m_minus = bin_points[m - 1]
        f_m = bin_points[m]
        f_m_plus = bin_points[m + 1]

        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - bin_points[m - 1]) / (bin_points[m] - bin_points[m - 1] + 1e-6)
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (bin_points[m + 1] - k) / (bin_points[m + 1] - bin_points[m] + 1e-6)
    return fbank, bin_points

fbank, bin_points = get_mel_filterbank(40, 512, 16000, 80, 7600)
hamming_win = np.hamming(480)

# Precompute DCT-II orthogonal basis for 40 filters x 40 coefficients
# formula: dct[m, k] = sqrt(2/N) * cos(pi * m * (2k + 1) / (2N)) (with sqrt(1/N) for m=0)
dct_matrix = np.zeros((40, 40), dtype=np.float32)
for m in range(40):
    factor = np.sqrt(1.0 / 40.0) if m == 0 else np.sqrt(2.0 / 40.0)
    for k in range(40):
        dct_matrix[m, k] = factor * np.cos(np.pi * m * (2 * k + 1) / (2.0 * 40.0))

print("Generating src/mfcc_tables.h ...")
with open("src/mfcc_tables.h", "w") as f:
    f.write("// AUTO-GENERATED MFCC AND FILTERBANK CONSTANTS FOR ESP32-S3\n")
    f.write("#ifndef MFCC_TABLES_H_\n#define MFCC_TABLES_H_\n\n#include <stdint.h>\n\n")
    
    f.write("const float hamming_window[480] = {\n  ")
    for i, val in enumerate(hamming_win):
        f.write(f"{val:.6f}f, ")
        if (i + 1) % 8 == 0: f.write("\n  ")
    f.write("\n};\n\n")
    
    # Store sparse bounds for each filter: start_bin, end_bin
    f.write("struct MelFilterBound { int16_t start; int16_t end; };\n")
    f.write("const MelFilterBound mel_filter_bounds[40] = {\n")
    for m in range(40):
        f.write(f"  {{ {bin_points[m]}, {bin_points[m+2]} }},\n")
    f.write("};\n\n")

    f.write("const float mel_fbank_weights[40][257] = {\n")
    for m in range(40):
        f.write("  { ")
        for k in range(257):
            f.write(f"{fbank[m, k]:.5f}f, ")
            if (k + 1) % 12 == 0: f.write("\n    ")
        f.write("},\n")
    f.write("};\n\n")

    f.write("const float dct_basis[40][40] = {\n")
    for m in range(40):
        f.write("  { ")
        for k in range(40):
            f.write(f"{dct_matrix[m, k]:.6f}f, ")
            if (k + 1) % 8 == 0: f.write("\n    ")
        f.write("},\n")
    f.write("};\n\n")

    f.write("#endif // MFCC_TABLES_H_\n")

print("Generated src/mfcc_tables.h successfully!")
