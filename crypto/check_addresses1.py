from tqdm import tqdm
import subprocess
import pickle
from difflib import SequenceMatcher

seqmatches = []
goal = '903408ec4d951acfaeb47ca88390c475'

with open('submatches.p', 'rb') as fp:
    valid_addresses = pickle.load(fp)

##try:
##    with open ('submatches.p', 'rb') as fp:
##        submatches = pickle.load(fp)
##except FileNotFoundError:
##    submatches = []
##
##try:
##    with open ('seqmatches.p', 'rb') as fp:
##        seqmatches = pickle.load(fp)
##except FileNotFoundError:
##    seqmatches = []

try:
    for i in tqdm(range(len(valid_addresses))):
        address = valid_addresses[i]
        addr_enc = address.encode('UTF-8')
        addr_hex = addr_enc.hex()

        if len(addr_hex) != 32:
            print("input doesnt conform, skipping")
            continue

        output = subprocess.check_output(["encrypt.exe", addr_hex])
        output = str(output)[2:-5]

        print("input: {}, output: {}".format(address, output))

        if output == goal:
            print("ADDRESS FOUND!!! \naddress =", address)
            exit(0)
        else:
            diff1 = SequenceMatcher(None, goal, output)
            diff1_ratio = diff1.ratio()
            diff2 = SequenceMatcher(None, output, goal)
            diff2_ratio = diff2.ratio()

            if 0.5 < diff1_ratio >= diff2_ratio:
                seqmatch = {'input': address, 'output': output, 'ratio': diff1_ratio,
                            'longest match': diff1.find_longest_match()}
                seqmatches.append(seqmatch)
                print("Seqmatch found:", seqmatch)
            elif 0.5 < diff2_ratio:
                seqmatch = {'input': address, 'output': output, 'ratio': diff2_ratio,
                            'longest match': diff2.find_longest_match()}
                seqmatches.append(seqmatch)
                print("Seqmatch found:", seqmatch)

except KeyboardInterrupt:
    print("Keyboard Interrupt!!")
    print("Halted on iteration:", i)
    print("Sequences with similarity ratio >50%:", seqmatches)

    with open('seqmatches.p', 'wb') as fp:
        pickle.dump(seqmatches, fp)

except Exception:
    print(Exception)
    print("Halted on iteration:", i)
    print("Sequences with similarity ratio >50%:", seqmatches)

    with open('seqmatches.p', 'wb') as fp:
        pickle.dump(seqmatches, fp)

print("Sequences with similarity ratio >50%:", seqmatches)

with open('seqmatches.p', 'wb') as fp:
    pickle.dump(seqmatches, fp)