import what3words
from tqdm import tqdm
import subprocess
import pickle


key = "1T7OBHEH"
geocoder = what3words.Geocoder(key)


addresses, valid_addresses, all_words, words4, words5, words6 = [], [], [], [], [], []

with open("top1000_words.txt") as fp:
    for line in fp:
        word = line.strip()

        if word[0].islower() and word not in all_words:
            all_words.append(word)

            # if len(word) == 4:
            #     words4.append(word)
            # elif len(word) == 5:
            #     words5.append(word)
            # elif len(word) == 6:
            #     words6.append(word)

print("all words:", all_words)
# print("4 letter words:", words4)
# print("5 letter words:", words5)
# print("6 letter words:", words6)

# or just select 1 word find addresses for 'word..' '.word.' '..word' which have length of 16 (incl. dots)
for i in tqdm(range(len(all_words))):
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

                if len(address) == 16 and address not in valid_addresses:
                    valid_addresses.append(address)
    except KeyboardInterrupt:
        print("Keyboard interrupt!")
        print("Current word:", word)
        print("Valid addresses:", valid_addresses)
        exit(1)

with open('addresses.p', 'wb') as fp:
    pickle.dump(valid_addresses, fp)

# with open ('addresses.p', 'rb') as fp:
#     valid_addresses = pickle.load(fp)

Key
