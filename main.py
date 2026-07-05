import os
import glob
import base64
import json
import msgpack
import re

# Keystream Universal (Hasil XOR dari Plaintext MessagePack vs Ciphertext)
UNIVERSAL_KS = bytes.fromhex("6ed0af75f064fab9b7aa84b6842f0f24d448dd694427f5dc69652c4cea04d4b057487656d5b9fc614a8111246fd1d94875ac8b750b1b3ae084e817034febbcaf81a26ad77a58671435c9cd592c8f5e572df3ca91db5a0cbe8704c0f07a5465b4553868d862533462e936bc032943df57e1d1c37dd5eb2e88fdc6fa277fe9f27a2824d203123881a2075750da25f73904e11aff45a30c37328b21f34aa0d41a2b6fd6dc67a41e05ef0ed56f42a1bfab668714cc8f21a5e377e43aad206e55fafa087328a51ca0a12007e482b15f4e196c0aaf67ff697b14453afb242fc2781d01fa5c13cc7c20fb4020f410493430acc453c6c5fc2168435abe831dd128ec8a25")

def fix_padding(s):
    return s + "=" * (4 - len(s) % 4) if len(s) % 4 else s

def decrypt_py_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().strip()
    
    if content.startswith("darktunnel://"):
        content = content[len("darktunnel://"):]
    
    # 1. Outer Layer (JSON)
    main_json = json.loads(base64.urlsafe_b64decode(fix_padding(content)))
    elc_b64 = main_json.get("encryptedLockedConfig")
    
    if isinstance(elc_b64, str) and len(elc_b64) > 20:
        # 2. Inner Layer (XOR Keystream)
        blob = base64.urlsafe_b64decode(fix_padding(elc_b64))
        
        # Dekripsi dengan XOR universal keystream
        decrypted_bin = bytes([blob[i] ^ UNIVERSAL_KS[i % len(UNIVERSAL_KS)] for i in range(len(blob))])
        
        # 3. MessagePack Unpack
        try:
            unpacker = msgpack.Unpacker(raw=False)
            unpacker.feed(decrypted_bin)
            main_json["encryptedLockedConfig"] = next(unpacker)
        except Exception:
            text = decrypted_bin.decode('utf-8', errors='ignore')
            json_match = re.search(r'(\{.*\})', text)
            main_json["encryptedLockedConfig"] = json.loads(json_match.group(1)) if json_match else text
            
    return main_json

def process_batch():
    input_folder = "."  # Baca file di direktori root / luar
    output_folder = "decrypt"

    # Buat direktori decrypt untuk hasil, dan encrypt untuk testing re-enkripsi kamu nanti
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs("encrypt", exist_ok=True)

    # Ambil SEMUA file berekstensi .dark di direktori saat ini
    # Ini juga akan aman menangani nama file dengan spasi atau emoji
    files_to_process = glob.glob(os.path.join(input_folder, "*.dark"))

    if not files_to_process:
        print("[*] Tidak ada file .dark yang ditemukan di direktori saat ini.")
        return

    print(f"[*] Menemukan {len(files_to_process)} file .dark. Memulai dekripsi...\n")

    for file_path in files_to_process:
        filename = os.path.basename(file_path)
        name_only, _ = os.path.splitext(filename)
        
        # Simpan hasil dekripsi di folder /decrypt/
        output_file_path = os.path.join(output_folder, f"{name_only}_decrypted.json")

        try:
            print(f" -> Memproses: {filename} ...", end=" ")
            
            decrypted_data = decrypt_py_file(file_path)

            with open(output_file_path, 'w', encoding='utf-8') as out_f:
                json.dump(decrypted_data, out_f, indent=4)
            
            print("BERHASIL")
        except Exception as e:
            print(f"GAGAL (Error: {e})")

    print("\n[*] Proses batch selesai! File JSON ada di folder 'decrypt'.")

if __name__ == "__main__":
    process_batch()
