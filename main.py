import os
import glob
import base64
import json
import re
from Crypto.Cipher import ChaCha20

# Master Key yang diderivasi dari HKDF (100% Valid untuk semua file .dark)
MASTER_KEY = bytes.fromhex("753872c6c6ec84b4cc8fa89ec76e19af920ecfb08200cae38c3110de1f29727e")

def decrypt_dark_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().strip()
    
    if content.startswith("darktunnel://"):
        content = content[len("darktunnel://"):]
    
    # 1. Dekode Base64 Luar
    missing_padding = len(content) % 4
    if missing_padding: content += "=" * (4 - missing_padding)
    main_json = json.loads(base64.urlsafe_b64decode(content))
    
    elc_b64 = main_json.get("encryptedLockedConfig")
    if isinstance(elc_b64, str) and len(elc_b64) > 20:
        # 2. Dekode Blob Biner
        missing_padding_inner = len(elc_b64) % 4
        if missing_padding_inner: elc_b64 += "=" * (4 - missing_padding_inner)
        blob = base64.urlsafe_b64decode(elc_b64)
        
        nonce = blob[:12]     # 12 byte pertama = Nonce
        ciphertext = blob[12:] # Sisanya = Ciphertext
        
        # 3. Dekripsi ChaCha20
        cipher = ChaCha20.new(key=MASTER_KEY, nonce=nonce)
        decrypted_bytes = cipher.decrypt(ciphertext)
        
        # 4. Pembersihan & Parsing JSON Internal
        try:
            text = decrypted_bytes.decode('utf-8', errors='ignore')
            # Mencari struktur JSON valid di dalam tumpukan byte
            json_match = re.search(r'(\{.*\})', text)
            if json_match:
                main_json["encryptedLockedConfig"] = json.loads(json_match.group(1))
            else:
                main_json["encryptedLockedConfig"] = text
        except:
            main_json["encryptedLockedConfig"] = "DECRYPTION_FAILED_PARSE"
            
    return main_json

if __name__ == "__main__":
    # 1. Pastikan folder decrypt ada
    os.makedirs("decrypt", exist_ok=True)
    
    # 2. Cari semua file .dark di direktori tempat script ini dijalankan
    files_to_process = glob.glob("*.dark")
    
    if not files_to_process:
        print("[*] Tidak ada file .dark yang ditemukan di direktori ini.")
    else:
        print(f"[*] Menemukan {len(files_to_process)} file. Memulai dekripsi...\n")
        
        for f_path in files_to_process:
            # Ambil nama asli filenya saja (tanpa path)
            filename = os.path.basename(f_path)
            name_only, _ = os.path.splitext(filename)
            
            print(f" -> Memproses: {filename} ...", end=" ")
            try:
                # Proses dekripsi
                result = decrypt_dark_file(f_path)
                
                # Buat jalur output ke folder decrypt/
                output_name = os.path.join("decrypt", f"{name_only}_decrypted.json")
                
                # Simpan hasilnya
                with open(output_name, "w", encoding='utf-8') as out_f:
                    json.dump(result, out_f, indent=4, ensure_ascii=False)
                
                print("OK")
            except Exception as e:
                print(f"FAILED: {e}")
                
        print("\n[*] Selesai! Silakan cek folder 'decrypt' untuk melihat hasil JSON.")
