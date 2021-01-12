import what3words
from tqdm import tqdm
import subprocess
import pickle

# gs_words = ["BAGS", "BEGS", "BIGS", "BOGS", "BUGS", "CAGS", "CIGS", "COGS", "DAGS",
#             "DEGS", "DIGS", "DOGS", "DUGS", "EGGS", "ENGS", "ERGS", "FAGS", "FEGS",
#             "FIGS", "FOGS", "FUGS", "GAGS", "GIGS", "HAGS", "HOGS", "HUGS", "IGGS",
#             "JAGS", "JIGS", "JOGS", "JUGS", "KEGS", "LAGS", "LEGS", "LIGS", "LOGS",
#             "LUGS", "MAGS", "MEGS", "MIGS", "MOGS", "MUGS", "NAGS", "NEGS", "NOGS",
#             "PEGS", "PIGS", "PUGS", "RAGS", "REGS", "RIGS", "RUGS", "SAGS", "SEGS",
#             "SOGS", "TAGS", "TEGS", "TIGS", "TOGS", "TUGS", "TYGS", "VAGS", "VIGS",
#             "VUGS", "WAGS", "WIGS", "WOGS", "YAGS", "YUGS", "ZAGS", "ZIGS"]

already_matched = ["body.cheese.bank", "body.cheese.bond", "body.cherry.body", "body.cherry.barn",
                   "bags.simmer.busy", "body.cherry.barn", "body.cheese.barn", "body.cheese.dawn"]

words4 = []

with open("dictionary_words.txt") as fp:
    for line in fp:
        word = line.strip()

        if word[0].islower() and len(word) == 4:
            words4.append(word)

addresses = []
count = 0

key = "1T7OBHEH"
geocoder = what3words.Geocoder(key)

for w1 in tqdm(range(len(words4))):

    with open('addresses9.p', 'wb') as fp:
        pickle.dump(addresses, fp)

    word1 = words4[w1]
    addr = word1 + ".simmer."

    for w2 in tqdm(range(32, len(words4))):
        address = addr + words4[w2]
        if len(address) == 16:
            addresses.append(address)
        else:
            continue
        count += 1

        res = geocoder.autosuggest(address, clip_to_country="GB", n_results=100)
        res = res['suggestions']

        for obj in res:
            addr = obj['words']

            if (len(addr) == 16) and (addr not in addresses) and (addr not in already_matched):
                addresses.append(addr)
                count += 1

print("{} matching addresses found".format(len(addresses)))

with open('addresses8.p', 'wb') as fp:
    pickle.dump(addresses, fp)
