#!/usr/bin/env python3
"""
Simple brain-wallet CLI: derive BTC (P2PKH, P2SH-P2WPKH, Bech32 P2WPKH) and ETH
addresses deterministically from an arbitrary passphrase using secp256k1.

SECURITY WARNING: Brain wallets based on human-chosen passphrases are insecure
and easily brute-forced. Use hardware wallets and BIP39 mnemonics generated
with strong entropy for real funds.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
from dataclasses import dataclass

# External deps kept minimal and common
from ecdsa import SECP256k1, SigningKey  # type: ignore
from Crypto.Hash import RIPEMD, keccak  # type: ignore


# ---------------------------- Utilities ------------------------------------

BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def ripemd160(data: bytes) -> bytes:
    h = RIPEMD.new()
    h.update(data)
    return h.digest()


def hash160(data: bytes) -> bytes:
    return ripemd160(sha256(data))


def base58check_encode(version: bytes, payload: bytes) -> str:
    raw = version + payload
    checksum = sha256(sha256(raw))[:4]
    data = raw + checksum

    # Convert to integer
    num = int.from_bytes(data, "big")

    # Encode in Base58
    encoded = bytearray()
    while num > 0:
        num, rem = divmod(num, 58)
        encoded.insert(0, BASE58_ALPHABET[rem])

    # Handle leading zeros
    zeros = 0
    for b in data:
        if b == 0:
            zeros += 1
        else:
            break
    return (BASE58_ALPHABET[0:1] * zeros + encoded).decode("ascii")


# --- Bech32 (BIP-0173) minimal implementation for P2WPKH -------------------

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_polymod(values: list[int]) -> int:
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ v
        for i in range(5):
            chk ^= generator[i] if ((b >> i) & 1) else 0
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _bech32_create_checksum(hrp: str, data: list[int]) -> list[int]:
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _bech32_encode(hrp: str, data: list[int]) -> str:
    combined = data + _bech32_create_checksum(hrp, data)
    return hrp + "1" + "".join([BECH32_CHARSET[d] for d in combined])


def _convertbits(data: bytes, frombits: int, tobits: int, pad: bool = True) -> list[int]:
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for b in data:
        if b < 0 or (b >> frombits):
            return []
        acc = ((acc << frombits) | b) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return []
    return ret


# ---------------------------- Core logic ------------------------------------


def derive_private_key(passphrase: str) -> bytes:
    return sha256(passphrase.encode("utf-8"))


def private_key_to_wif(priv_key: bytes, compressed: bool = True, mainnet: bool = True) -> str:
    version = b"\x80" if mainnet else b"\xef"
    payload = priv_key + (b"\x01" if compressed else b"")
    return base58check_encode(version, payload)


def private_to_pubkey_compressed(priv_key: bytes) -> bytes:
    sk = SigningKey.from_string(priv_key, curve=SECP256k1)
    vk = sk.get_verifying_key()
    x_bytes = vk.pubkey.point.x().to_bytes(32, "big")
    y = vk.pubkey.point.y()
    prefix = b"\x02" if y % 2 == 0 else b"\x03"
    return prefix + x_bytes


def btc_p2pkh_address(pubkey_compressed: bytes, mainnet: bool = True) -> str:
    vh160 = (b"\x00" if mainnet else b"\x6f") + hash160(pubkey_compressed)
    return base58check_encode(b"", vh160)  # version is already included in vh160


def btc_p2sh_p2wpkh_address(pubkey_compressed: bytes, mainnet: bool = True) -> str:
    # redeemScript = 0x00 PUSH_DATA(20) <hash160(pubkey)>
    redeem = b"\x00\x14" + hash160(pubkey_compressed)
    version = b"\x05" if mainnet else b"\xc4"  # P2SH version
    return base58check_encode(version, hash160(redeem))


def btc_bech32_p2wpkh_address(pubkey_compressed: bytes, hrp: str = "bc") -> str:
    prog = hash160(pubkey_compressed)
    data = [0] + _convertbits(prog, 8, 5)
    return _bech32_encode(hrp, data)


def eth_address_from_privkey(priv_key: bytes) -> tuple[str, str]:
    sk = SigningKey.from_string(priv_key, curve=SECP256k1)
    vk = sk.get_verifying_key()
    # Uncompressed public key (no 0x04 prefix)
    x = vk.pubkey.point.x().to_bytes(32, "big")
    y = vk.pubkey.point.y().to_bytes(32, "big")
    pub_bytes_no_prefix = x + y

    k = keccak.new(digest_bits=256)
    k.update(pub_bytes_no_prefix)
    digest = k.digest()
    raw_addr = digest[-20:]
    hex_addr = raw_addr.hex()

    # EIP-55 checksum
    k2 = keccak.new(digest_bits=256)
    k2.update(hex_addr.encode("ascii"))
    addr_hash = k2.hexdigest()
    checksummed = "0x" + "".join(
        (c.upper() if int(addr_hash[i], 16) >= 8 else c)
        for i, c in enumerate(hex_addr)
    )

    # Public key hex (uncompressed with 0x04 prefix)
    pub_uncompressed_hex = "04" + pub_bytes_no_prefix.hex()
    return checksummed, pub_uncompressed_hex


@dataclass
class WalletResult:
    priv_hex: str
    wif: str
    pubkey_hex_compressed: str
    btc_p2pkh: str
    btc_p2sh_p2wpkh: str
    btc_bech32: str
    eth_address: str
    eth_pub_uncompressed: str


def generate_from_passphrase(passphrase: str) -> WalletResult:
    priv = derive_private_key(passphrase)
    priv_hex = priv.hex()
    wif = private_key_to_wif(priv, compressed=True, mainnet=True)
    pub_c = private_to_pubkey_compressed(priv)
    p2pkh = btc_p2pkh_address(pub_c)
    p2sh_p2wpkh = btc_p2sh_p2wpkh_address(pub_c)
    bech32 = btc_bech32_p2wpkh_address(pub_c)
    eth_addr, eth_pub_uncompressed = eth_address_from_privkey(priv)
    return WalletResult(
        priv_hex=priv_hex,
        wif=wif,
        pubkey_hex_compressed=pub_c.hex(),
        btc_p2pkh=p2pkh,
        btc_p2sh_p2wpkh=p2sh_p2wpkh,
        btc_bech32=bech32,
        eth_address=eth_addr,
        eth_pub_uncompressed=eth_pub_uncompressed,
    )


# ------------------------------ CLI ----------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate BTC and ETH wallets from a passphrase (brain wallet)")
    parser.add_argument("--passphrase", "-p", help="Passphrase to derive keys from. If omitted, prompts interactively.")
    args = parser.parse_args()

    phrase = args.passphrase
    if not phrase:
        try:
            phrase = input("Enter passphrase: ")
        except EOFError:
            phrase = ""
    if phrase is None or phrase.strip() == "":
        print("Passphrase is empty. Aborting.")
        return

    res = generate_from_passphrase(phrase)

    print("\n[Bitcoin Wallet]")
    print(f"P2PKH address: {res.btc_p2pkh}")
    print(f"P2SH address: {res.btc_p2sh_p2wpkh}")
    print(f"BECH32 address: {res.btc_bech32}")
    print(f"public key: {res.pubkey_hex_compressed}")
    print(f"private key: {res.priv_hex}")
    print(f"WIF (compressed): {res.wif}")
    print(f"mnemonic: {phrase}")

    print("\n[EVM/Ethereum Wallet]")
    print(f"address: {res.eth_address}")
    print(f"public key: {res.eth_pub_uncompressed}")
    print(f"private key: {res.priv_hex}")
    print(f"mnemonic: {phrase}")


if __name__ == "__main__":
    main()
