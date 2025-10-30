import os
import sys
import json
from typing import List, Optional

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

try:
    from bip_utils import (
        Bip39MnemonicGenerator,
        Bip39MnemonicValidator,
        Bip39SeedGenerator,
        Bip44,
        Bip44Coins,
        Bip44Changes,
        Bip49,
        Bip49Coins,
        Bip84,
        Bip84Coins,
    )
except Exception as e:  # pragma: no cover
    print("Error: missing crypto dependencies. Please install requirements.")
    print(str(e))
    sys.exit(1)


def prompt(prompt_text: str) -> str:
    try:
        return input(prompt_text)
    except EOFError:
        return ""


def prompt_int(prompt_text: str, default: int, min_value: int, max_value: int) -> int:
    while True:
        raw = prompt(f"{prompt_text} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = int(raw)
        except Exception:
            print("Please enter a number.")
            continue
        if value < min_value or value > max_value:
            print(f"Enter a value between {min_value} and {max_value}.")
            continue
        return value


def action_generate_mnemonic() -> None:
    print("\n== Generate BIP39 Mnemonic ==")
    word_count = prompt_int("Word count (12 or 24)", default=12, min_value=12, max_value=24)
    if word_count not in (12, 24):
        print("Only 12 or 24 words are supported.")
        return
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(word_count)
    print("\nMnemonic:")
    print(mnemonic)
    print("\nIMPORTANT: Store it securely. Anyone with this phrase can control funds.")


def action_validate_mnemonic() -> None:
    print("\n== Validate BIP39 Mnemonic ==")
    mnemonic = prompt("Enter mnemonic: ").strip()
    if mnemonic == "":
        print("Empty mnemonic.")
        return
    try:
        Bip39MnemonicValidator(mnemonic).Validate()
        print("Mnemonic is valid.")
    except Exception as e:
        print("Invalid mnemonic:", str(e))


def _derive_btc_addresses(
    mnemonic: str,
    passphrase: str,
    script_type: str,
    count: int,
) -> List[str]:
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase)
    addresses: List[str] = []

    if script_type == "p2pkh":
        ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    elif script_type == "p2sh-p2wpkh":
        ctx = Bip49.FromSeed(seed_bytes, Bip49Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    elif script_type == "bech32":
        ctx = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    else:
        raise ValueError("Unsupported BTC script type")

    for index in range(count):
        addr = ctx.AddressIndex(index).PublicKey().ToAddress()
        addresses.append(addr)
    return addresses


def _derive_evm_addresses(
    mnemonic: str,
    passphrase: str,
    chain: str,
    count: int,
) -> List[str]:
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase)

    # Choose coin type based on chain label; addresses are EVM-style
    chain_lower = chain.lower()
    if chain_lower in ("eth", "ethereum"):
        coin = Bip44Coins.ETHEREUM
    elif chain_lower in ("bsc", "bnb", "binance smart chain", "binance-smart-chain"):
        # EVM compatible
        coin = Bip44Coins.BINANCE_SMART_CHAIN
    elif chain_lower in ("polygon", "matic"):
        coin = Bip44Coins.POLYGON
    else:
        # Default to ETH (EVM) if unknown
        coin = Bip44Coins.ETHEREUM

    ctx = Bip44.FromSeed(seed_bytes, coin).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)

    addresses: List[str] = []
    for index in range(count):
        addr = ctx.AddressIndex(index).PublicKey().ToAddress()
        addresses.append(addr)
    return addresses


def action_derive_addresses() -> None:
    print("\n== Derive Addresses from Mnemonic ==")
    mnemonic = prompt("Enter mnemonic: ").strip()
    if mnemonic == "":
        print("Empty mnemonic.")
        return
    try:
        Bip39MnemonicValidator(mnemonic).Validate()
    except Exception as e:
        print("Invalid mnemonic:", str(e))
        return

    passphrase = prompt("Optional BIP39 passphrase (press Enter to skip): ")
    count = prompt_int("How many addresses?", default=5, min_value=1, max_value=50)

    print("\nSelect chain:")
    print("  1) Bitcoin (BTC)")
    print("  2) Ethereum (ETH)")
    print("  3) BNB Smart Chain (BSC)")
    print("  4) Polygon (MATIC)")
    chain_choice = prompt("Choice [1]: ").strip() or "1"

    if chain_choice == "1":
        print("\nBTC script type:")
        print("  1) Legacy P2PKH (m/44')")
        print("  2) Nested SegWit P2SH-P2WPKH (m/49')")
        print("  3) Native SegWit Bech32 (m/84')")
        st_choice = prompt("Choice [3]: ").strip() or "3"
        script_type = {"1": "p2pkh", "2": "p2sh-p2wpkh", "3": "bech32"}.get(st_choice, "bech32")
        addresses = _derive_btc_addresses(mnemonic, passphrase, script_type, count)
        print("\nDerived BTC addresses:")
        for i, addr in enumerate(addresses):
            print(f"[{i}] {addr}")
    else:
        chains = {"2": "ETH", "3": "BSC", "4": "POLYGON"}
        chain_label = chains.get(chain_choice, "ETH")
        addresses = _derive_evm_addresses(mnemonic, passphrase, chain_label, count)
        print(f"\nDerived {chain_label} addresses:")
        for i, addr in enumerate(addresses):
            print(f"[{i}] {addr}")


def _eth_get_balance(rpc_url: str, address: str) -> Optional[int]:
    if requests is None:
        print("requests library not available.")
        return None
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1,
        }
        resp = requests.post(rpc_url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "result" in data and isinstance(data["result"], str):
            return int(data["result"], 16)
    except Exception as e:
        print("Error querying EVM RPC:", str(e))
    return None


def _btc_get_balance(address: str) -> Optional[int]:
    if requests is None:
        print("requests library not available.")
        return None
    # Uses Blockstream public API (mainnet)
    url = f"https://blockstream.info/api/address/{address}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        chain_stats = data.get("chain_stats", {})
        funded = int(chain_stats.get("funded_txo_sum", 0))
        spent = int(chain_stats.get("spent_txo_sum", 0))
        return max(0, funded - spent)
    except Exception as e:
        print("Error querying Blockstream API:", str(e))
        return None


def action_check_balance() -> None:
    print("\n== Check Address Balance (User-supplied) ==")
    print("This only checks addresses you explicitly provide.")

    print("\nSelect network:")
    print("  1) Bitcoin (BTC)")
    print("  2) EVM (ETH/BNB/MATIC via RPC)")
    net_choice = prompt("Choice [1]: ").strip() or "1"

    address = prompt("Enter address: ").strip()
    if address == "":
        print("Empty address.")
        return

    if net_choice == "1":
        satoshi = _btc_get_balance(address)
        if satoshi is None:
            return
        btc = satoshi / 1e8
        print(f"Balance: {btc:.8f} BTC ({satoshi} sats)")
    else:
        rpc_url = os.getenv("EVM_RPC_URL") or prompt("Enter EVM RPC URL (e.g., Infura/Alchemy): ").strip()
        if rpc_url == "":
            print("No RPC URL provided.")
            return
        wei = _eth_get_balance(rpc_url, address)
        if wei is None:
            return
        eth = wei / 1e18
        print(f"Balance: {eth:.18f} ETH (wei: {wei})")


def main() -> None:
    while True:
        print("\n==================== WalletGen (Safe CLI) ====================")
        print("  1) Generate BIP39 mnemonic")
        print("  2) Validate mnemonic")
        print("  3) Derive addresses (BTC/EVM)")
        print("  4) Check balance for provided address")
        print("  5) Exit")
        choice = prompt("Select option [1-5]: ").strip()
        if choice == "1":
            action_generate_mnemonic()
        elif choice == "2":
            action_validate_mnemonic()
        elif choice == "3":
            action_derive_addresses()
        elif choice == "4":
            action_check_balance()
        elif choice == "5":
            print("Goodbye.")
            break
        else:
            print("Unknown choice. Please select 1, 2, 3, 4, or 5.")


if __name__ == "__main__":
    main()
