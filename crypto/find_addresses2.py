import what3words
from tqdm import tqdm
import subprocess
import pickle


key = "1T7OBHEH"
geocoder = what3words.Geocoder(key)

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

with open('addresses4.p', 'wb') as fp:
    pickle.dump(addresses, fp)
