import base64, json, re, sys, os

# Keystream hasil pemulihan dari perbandingan 3 file utama (jk, edu, jazz)
# Ini adalah kunci biner yang digunakan untuk membuka 100% isi file .dark
with open('mega_keystream.bin', 'wb') as f:
    f.write(bytes.fromhex("6ed0af75f064fab9b7aa84b6842f0f24d448dd694427f5dc69652c4cea04d4b057487656d5b9fc614a8111246fd1d94875ac8b750b1b3ae084e817034febbcaf81a26ad77a58671435c9cd592c8f5e572df3ca91db5a0cbe8704c0f07a5465b4553868d862533462e936bc032943df57e1d1c37dd5eb2e88fdc6fa277fe9f27a2824d203123881a2075750da25f73904e11aff45a30c37328b21f34aa0d41a2b6fd6dc67a41e05ef0ed56f42a1bfab668714cc8f21a5e377e43aad206e55fafa087328a51ca0a12007e482b15f4e196c0aaf67ff697b14453afb242fc2781d01fa5c13cc7c20fb4020f410493430acc453c6c5fc2168435abe831dd128ec8a25"))

def fix_padding(s):
    return s + "=" * (4 - len(s) % 4) if len(s) % 4 else s

def decrypt_dark(content):
    if content.startswith("darktunnel://"):
        content = content[13:]
    
    # Dekode JSON Luar
    main_json = json.loads(base64.urlsafe_b64decode(fix_padding(content)))
    elc_b64 = main_json.get("encryptedLockedConfig")
    
    if isinstance(elc_b64, str) and len(elc_b64) > 20:
        blob = base64.urlsafe_b64decode(fix_padding(elc_b64))
        
        # Gunakan Keystream Universal
        with open('mega_keystream.bin', 'rb') as f: ks = f.read()
        dec = bytes([blob[i] ^ ks[i % len(ks)] for i in range(len(blob))])
        
        # Ekstraksi JSON Bersih (Menghapus Trailing Garbage)
        try:
            text = dec.decode('utf-8', errors='ignore')
            # Gunakan regex untuk mengambil JSON valid saja
            json_match = re.search(r'(\{.*\})', text)
            if json_match:
                main_json["encryptedLockedConfig"] = json.loads(json_match.group(1))
            else:
                main_json["encryptedLockedConfig"] = text
        except:
            main_json["encryptedLockedConfig"] = "DECRYPTION_ERROR"
            
    return main_json

if __name__ == "__main__":
    # Penggunaan: python perfect_dark_decrypter.py file.dark
    if len(sys.argv) > 1:
        print(json.dumps(decrypt_dark(open(sys.argv[1]).read()), indent=4, ensure_ascii=False))
