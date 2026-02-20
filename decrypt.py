import os
import struct
import argparse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

KEY_MATERIAL1 = bytes.fromhex("D98633AC10EB3D600FBECBA023FADF58")
KEY_MATERIAL2 = bytes.fromhex("B3BC4F5C8FBFC6B2126A50EFAE032210")

backend = default_backend()

def aes_ecb_encrypt(key: bytes, data: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()

def aes_ecb_decrypt(key: bytes, data: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)
    decryptor = cipher.decryptor()
    return decryptor.update(data) + decryptor.finalize()

POLY = 0x87

def gmul_x(block: bytearray) -> int:
    carry = 0
    for i in range(len(block)):
        next_carry = block[i] >> 7
        block[i] = ((block[i] << 1) & 0xFF) | carry
        carry = next_carry
    if carry:
        block[0] ^= POLY
    return carry

def gmul_x_inv(block: bytearray, carry_in: int):
    if carry_in:
        block[0] ^= POLY
    carry = carry_in
    for i in range(len(block)-1, -1, -1):
        low_bit = block[i] & 1
        block[i] = (block[i] >> 1) | (carry << 7)
        carry = low_bit

def process_block(data: bytearray, offset: int, ks: bytearray, is_encrypt: bool):
    sub = data[offset:offset+16]
    for i in range(16):
        sub[i] ^= ks[i]
    if is_encrypt:
        transformed = aes_ecb_encrypt(KEY_MATERIAL1, bytes(sub))
    else:
        transformed = aes_ecb_decrypt(KEY_MATERIAL1, bytes(sub))
    transformed = bytearray(transformed)
    for i in range(16):
        transformed[i] ^= ks[i]
    data[offset:offset+16] = transformed

def verify_size(input_path: str, data: bytes, init_ks: bytes):
    buf = bytearray(data)
    length = len(buf)
    block_size = 16
    num_full = length // block_size
    if num_full == 0:
        raise ValueError("文件大小必须至少为16字节！")

def process_chunk(data: bytes, init_ks: bytes, is_encrypt: bool) -> bytes:
    ks = bytearray(init_ks)
    buf = bytearray(data)
    length = len(buf)
    block_size = 16
    num_full = length // block_size
    rem = length % block_size

    for i in range(num_full - 1):
        offset = i * block_size
        process_block(buf, offset, ks, is_encrypt)
        gmul_x(ks)

    last_offset = (num_full - 1) * block_size
    has_rem = rem > 0

    if has_rem:
        if is_encrypt:
            carry = gmul_x(ks)
            process_block(buf, last_offset, ks, is_encrypt)
            gmul_x_inv(ks, carry)
        else:
            process_block(buf, last_offset, ks, is_encrypt)
            gmul_x(ks)
        start1 = last_offset
        len1 = rem
        start2 = last_offset + block_size
        len2 = length - start2
        if len2 > 0:
            tmp1 = buf[start1:start1+len1]
            tmp2 = buf[start2:start2+len2]
            buf[start1:start1+len1] = tmp2
            buf[start2:start2+len2] = tmp1
        process_block(buf, last_offset, ks, is_encrypt)
    else:
        process_block(buf, last_offset, ks, is_encrypt)

    return bytes(buf)

def decrypt_file(input_path: str, output_path: str):
    with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
        block_idx = 0
        while True:
            chunk = fin.read(512)
            if not chunk:
                break
            counter = struct.pack('<Q', block_idx) + b'\x00' * 8
            init_ks = aes_ecb_encrypt(KEY_MATERIAL2, counter)
            verify_size(input_path, chunk, init_ks)
            plain = process_chunk(chunk, init_ks, is_encrypt=False)
            fout.write(plain)
            block_idx += 1
    print(f"解密成功: {output_path}")

def encrypt_file(input_path: str, output_path: str):
    with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
        block_idx = 0
        while True:
            chunk = fin.read(512)
            if not chunk:
                break
            counter = struct.pack('<Q', block_idx) + b'\x00' * 8
            init_ks = aes_ecb_encrypt(KEY_MATERIAL2, counter)
            verify_size(input_path, chunk, init_ks)
            cipher = process_chunk(chunk, init_ks, is_encrypt=True)
            fout.write(cipher)
            block_idx += 1
    print(f"加密成功: {output_path}")

def batch_decrypt(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        in_path = os.path.join(input_dir, filename)
        out_path = os.path.join(output_dir, filename)
        if os.path.isfile(in_path):
            try:
                decrypt_file(in_path, out_path)
            except Exception as e:
                print(f"解密失败 {filename}: {e}")

def batch_encrypt(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        in_path = os.path.join(input_dir, filename)
        out_path = os.path.join(output_dir, filename)
        if os.path.isfile(in_path):
            try:
                encrypt_file(in_path, out_path)
            except Exception as e:
                print(f"加密失败 {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="资源加密/解密工具")
    parser.add_argument("mode", choices=["decrypt", "encrypt"], help="操作模式")
    parser.add_argument("input", help="输入文件或目录")
    parser.add_argument("output", help="输出文件或目录")
    parser.add_argument("--batch", action="store_true", help="批量处理目录")
    args = parser.parse_args()

    if args.batch:
        if args.mode == "decrypt":
            batch_decrypt(args.input, args.output)
        else:
            batch_encrypt(args.input, args.output)
    else:
        if args.mode == "decrypt":
            decrypt_file(args.input, args.output)
        else:
            encrypt_file(args.input, args.output)