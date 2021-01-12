import what3words
from tqdm import tqdm
import subprocess
import pickle


key = "1T7OBHEH"
geocoder = what3words.Geocoder(key)

"""
addresses3, all_words = [], []

with open("crypto/dictionary_words.txt") as fp:
    for line in fp:
        word = line.strip()

        if word[0].islower() and word not in all_words:
            all_words.append(word)


with open('crypto/addresses1.p', 'rb') as fp:
    addresses1 = pickle.load(fp)

with open('crypto/addresses2.p', 'rb') as fp:
    addresses2 = pickle.load(fp)
"""


addresses = ["body.cheese.bank", "body.cheese.bond", "body.cherry.body", "bags.simmer.busy"]
matching_addresses = []

for address in addresses:
    res = geocoder.autosuggest(address, clip_to_country="GB", n_results=100)
    res = res['suggestions']

    for obj in res:
        addr = obj['words']

        if (len(addr) == 16) and (addr not in addresses):
            matching_addresses.append(addr)


"""
# searching for matching substrings in addresses
# substrings = ['ba', 'ag', 'gs', 's.', '.s', 'si', 'im', 'mm', 'me', 'er', 'r.', '.b', 'bu', 'us', 'sy']
substrings = ['me']
output = []
addresses = []

print("searching addresses1 for submatches")
for i in tqdm(range(len(addresses1))):
    address = addresses1[i]
    out = {'address': address, 'matches': []}

    for string in substrings:
        if string in address:
            out['matches'].append(string)

    if len(out['matches']) > 0:
        output.append(out)

print("\nsearching addresses2 for submatches")
for j in tqdm(range(len(addresses2))):
    address = addresses2[j]
    out = {'address': address, 'matches': []}

    for string in substrings:
        if string in address:
            out['matches'].append(string)

    if len(out['matches']) > 0:
        output.append(out)
        addresses.append(address)

print("Found {} addresses with submatches".format(len(addresses)))

with open('crypto/submatches.p', 'wb') as fp:
    pickle.dump(addresses, fp)
"""

"""
# select 1 word find addresses for 'word..' '.word.' '..word' which have length of 16 (incl. dots)
# start from 15000 because i have already populated the array with 0-~15000
for i in tqdm(range(15000, len(all_words))):

    if i % 100:
        with open('crypto/addresses3.p', 'wb') as fp:
            pickle.dump(addresses3, fp)

    word = all_words[i]
    address1 = word + ".."
    address2 = "." + word + '.'
    address3 = ".." + word
    addresses = [address1, address2, address3]

    try:
        for addr in addresses:
            res = geocoder.autosuggest(addr, clip_to_country="GB", n_results=100)
            res = res['suggestions']

            for obj in res:
                address = obj['words']

                if (len(address) == 16) and (address not in addresses1) and (address not in addresses2) and (address not in addresses3):
                    addresses3.append(address)

    except KeyboardInterrupt:
        print("Keyboard interrupt!")
        print("Current word:", word)
        print("Valid addresses:", addresses3)

        with open('crypto/addresses3.p.', 'wb') as fp:
            pickle.dump(addresses3, fp)

        exit(1)

    except (ConnectionError, ConnectionResetError):
        print("Connection error :(")
        print("Current word:", word)
        print("Valid addresses:", addresses3)

        with open('crypto/addresses3.p', 'wb') as fp:
            pickle.dump(addresses3, fp)

with open('crypto/addresses3.p', 'wb') as fp:
    pickle.dump(addresses3, fp)

print("More addresses:\n", addresses3)
"""