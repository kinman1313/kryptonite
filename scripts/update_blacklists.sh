#!/bin/bash
curl -s https://www.treasury.gov/ofac/downloads/sdnlist.txt | grep -Ei "(BTC|ETH)" >../blacklist.txt
curl -s https://raw.githubusercontent.com/cryptoscamdb/cryptoscamdb/master/blacklist/addresses.json | jq -r 'keys[]' >>../blacklist.txt
sort -u -o ../blacklist.txt ../blacklist.txt
