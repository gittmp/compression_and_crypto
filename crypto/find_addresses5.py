import what3words
from tqdm import tqdm
import pickle


che_words = []
with open("che_len6.txt") as fp:
    for line in fp:
        word = line.strip()

        if word[0].islower():
            che_words.append(word)

addresses = []
count = 0

key = "1T7OBHEH"
geocoder = what3words.Geocoder(key)

for w in tqdm(range(len(che_words))):

    with open('addresses10.p', 'wb') as fp:
        pickle.dump(addresses, fp)

    word2 = che_words[w]
    address = "body." + word2 + "."

    res = geocoder.autosuggest(address, clip_to_country="GB", n_results=100)
    res = res['suggestions']

    for obj in res:
        addr = obj['words']

        if (addr[:8] == "body.che") and (len(addr) == 16) and (addr not in addresses):
            addresses.append(addr)
            count += 1

print("{} matching addresses found:".format(len(addresses)))
print(addresses)

with open('addresses10.p', 'wb') as fp:
    pickle.dump(addresses, fp)

