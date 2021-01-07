import what3words
from tqdm import tqdm
import subprocess
import pickle


key = "1T7OBHEH"
geocoder = what3words.Geocoder(key)

addresses, all_words = [], []

with open("dictionary_words.txt") as fp:
    for line in fp:
        word = line.strip()

        if word[0].islower() and word not in all_words:
            all_words.append(word)

with open('addresses.p', 'rb') as fp:
    valid_addresses = pickle.load(fp)

with open('more_addresses.p', 'rb') as fp:
    more_addresses = pickle.load(fp)

# select 1 word find addresses for 'word..' '.word.' '..word' which have length of 16 (incl. dots)
# start from 15000 because i have already populated the array with 0-~15000
for i in tqdm(range(15000, len(all_words))):

    if i % 100:
        with open('more_addresses.p', 'wb') as fp:
            pickle.dump(more_addresses, fp)

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

                if len(address) == 16 and address not in valid_addresses and address not in more_addresses:
                    more_addresses.append(address)

    except KeyboardInterrupt:
        print("Keyboard interrupt!")
        print("Current word:", word)
        print("Valid addresses:", more_addresses)

        with open('more_addresses.', 'wb') as fp:
            pickle.dump(more_addresses, fp)

        exit(1)

    except (ConnectionError, ConnectionResetError):
        print("Connection error :(")
        print("Current word:", word)
        print("Valid addresses:", more_addresses)

        with open('more_addresses2.p', 'wb') as fp:
            pickle.dump(more_addresses, fp)

with open('more_addresses.p', 'wb') as fp:
    pickle.dump(more_addresses, fp)

print("More addresses:\n", more_addresses)
