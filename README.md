# Anemic royalty's Nicehash Linux client

A completely unofficial Linux client for Nicehash.

# Features
* Algorithm switching based on current prices.
* Continous benchmarking: uses real miners performance instead of a one-off benchmark.
* Workers: ability to group multiple GPUs.
* Custom commands: performing custom commands either before and/or after a miner finishes. Useful for tailored overclocking for
some algorithms.
* Switching statistics: keeps track of algorithm switching and whether they were switched out of while having at least one accepted share or not.

# Requirements
* Python 3
* Python "requests" module. Available in your distro's package manager.

# Required miners
* ccminer. I'm using Tanguy Pruvot's fork https://github.com/tpruvot/ccminer, but other forks should work as well (as long as 
hey don't customize the output and support required algorithms).
* ethminer. https://github.com/ethereum-mining/ethminer
* dstm's ZCash miner for equihash. Unfortunately closed source, but it seems to be the fastest one out there. 
https://bitcointalk.org/index.php?topic=2021765.0


Their binaries must be in your PATH, otherwise the program won't be able to launch them.

# Configuration
Read through the configuration file (arnl.cfg) as it is pretty heavily commented.
After a one-off benchmark or each session is finished, a new configuration file is created with updated performance numbers.
The file is "updated.cfg" and as long as it is in the same folder as the main configation file, the main configuration file
is disregarded and any changes made to it won't be reflected. You can of course modify the "updated.cfg", the structure
is the same.

# Usage
After the initial configuration is finished, just make the nicehash.py executable and run it in a terminal.
Turn the program off by sending CTRL+C. 
