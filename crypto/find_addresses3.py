import what3words
from tqdm import tqdm
import subprocess
import pickle


key = "1T7OBHEH"
geocoder = what3words.Geocoder(key)

already_matched = ["body.cheese.bank", "body.cheese.bond", "body.cherry.body", "body.cherry.barn",
                   "bags.simmer.busy", "body.cherry.barn", "body.cheese.barn", "body.cheese.dawn"]

# addresses = ["body.cheese.bank", "body.cheese.bond", "body.cherry.body", "bags.simmer.busy",
#              "bank.cheese.body", "bond.cheese.body", "body.cherry.bank", "bank.cherry.body",
#              "bond.cheese.bond", "bank.cheese.bank", "body.cherry.bond", "bond.cherry.body",
#              "bond.cherry.bond", "bank.cherry.bank", "bags.simmer.busy", "busy.simmer.busy",
#              "body.simmer.busy", "bank.simmer.busy", "bond.simmer.busy", "bags.simmer.bags",
#              "bags.simmer.body", "bags.simmer.bank", "bags.simmer.bond", "busy.simmer.bags",
#              "busy.simmer.body", "busy.simmer.bank", "busy.simmer.bond", "body.simmer.bags",
#              "bank.simmer.bags", "bond.simmer.bags", "body.cherry.barn",
#              "barn.cheese.bank", "barn.cheese.bond", "barn.cherry.body", "barn.simmer.busy",
#              "barn.cheese.body", "barn.cheese.body", "barn.cherry.bank", "barn.cherry.body",
#              "barn.cheese.bond", "barn.cheese.bank", "barn.cherry.bond", "barn.cherry.body",
#              "barn.cherry.bond", "barn.cherry.bank", "barn.simmer.busy", "barn.simmer.busy",
#              "barn.simmer.busy", "barn.simmer.busy", "barn.simmer.busy", "barn.simmer.bags",
#              "barn.simmer.body", "barn.simmer.bank", "barn.simmer.bond", "barn.simmer.bags",
#              "barn.simmer.body", "barn.simmer.bank", "barn.simmer.bond", "barn.simmer.bags",
#              "barn.simmer.bags", "barn.simmer.bags",
#              "body.cheese.barn", "body.cheese.barn", "body.cherry.barn", "bags.simmer.barn",
#              "bank.cheese.barn", "bond.cheese.barn", "body.cherry.barn", "bank.cherry.barn",
#              "bond.cheese.barn", "bank.cheese.barn", "body.cherry.barn", "bond.cherry.barn",
#              "bond.cherry.barn", "bank.cherry.barn", "bags.simmer.barn", "busy.simmer.barn",
#              "body.simmer.barn", "bank.simmer.barn", "bond.simmer.barn", "bags.simmer.barn",
#              "bags.simmer.barn", "bags.simmer.barn", "bags.simmer.barn", "busy.simmer.barn",
#              "busy.simmer.barn", "busy.simmer.barn", "busy.simmer.barn", "body.simmer.barn",
#              "bank.simmer.barn", "bond.simmer.barn", "body.cherry.barn"]

# with open('addresses5.p', 'rb') as fp:
#     addresses = pickle.load(fp)

addresses = ["bags.simmer.busy", "bugs.simmer.busy", "sags.simmer.busy"]

matching_addresses = []
# matching_addresses.extend(addresses)

count = 0
for i in tqdm(range(len(addresses))):
    address = addresses[i]
    res = geocoder.autosuggest(address, clip_to_country="GB", n_results=100)
    res = res['suggestions']

    for obj in res:
        addr = obj['words']

        if (len(addr) == 16) and (addr not in addresses) and (addr not in matching_addresses) and (addr not in already_matched):
            matching_addresses.append(addr)
            count += 1

print("{} matching addresses: {}".format(count, matching_addresses))

with open('addresses6.p', 'wb') as fp:
    pickle.dump(matching_addresses, fp)
