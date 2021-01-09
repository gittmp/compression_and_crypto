import os
import sys
import math
import pickle


def find_bounds(t_bin, l_bin, h_bin, total):
    print("1) finding interval: binary tag = {}, low = {}, high = {}".format(t_bin, l_bin, h_bin))

    tg = int(t_bin, 2)
    l = int(l_bin, 2)
    h = int(h_bin, 2)
    low_bound, high_bound = 0, 0

    print(" a. int tag = {}, int low = {}, int high = {}".format(tg, l, h))

    # find frequency value
    frequency = math.floor(((tg - l + 1) * total - 1) / (h - l + 1))

    print(" b. decoded frequency = (({} - {} + 1) * {} - 1) / ({} - {} + 1) = {}".format(tg, l, total, h, l, frequency))

    # this is where you check what interval correlated to p
    # keys = list(table.keys())
    j = 0

    while frequency >= high_bound:
        low_bound = high_bound
        j += 1
        high_bound = j
        # low_bound = high_bound
        # high_bound = table[keys[j]]

    # symb = keys[j]
    symb = low_bound

    print(" c. found symbol = {}, interval = [{}/{}, {}/{}) = [{}, {})".format(repr(symb), low_bound, total, high_bound, total, low_bound/total, high_bound/total))

    low_bound = low_bound / total
    high_bound = high_bound / total

    return low_bound, high_bound, symb


def update_lh(t_bin, rem_tag, l_bin, h_bin, l_prob, h_prob):
    print("2) updating low and high bounds")

    l_old = int(l_bin, 2)
    h_old = int(h_bin, 2)

    l_new = l_old + math.floor((h_old - l_old + 1) * l_prob)
    h_new = l_old + math.floor((h_old - l_old + 1) * h_prob) - 1

    print(" a. low prob = {}, high prob = {}".format(l_prob, h_prob))
    print(" b. int l_old -> l_new: {} -> {}".format(l_old, l_new))
    print(" c. int h_old -> h_new: {} -> {}".format(h_old, h_new))

    l_new = format(l_new, 'b')
    l = l_new + '0' * (m - len(l_new))
    h_new = format(h_new, 'b')
    h = h_new + '1' * (m - len(h_new))

    print(" d. binary versions: l = {}, h = {}".format(l_new, h_new))
    print(" e. checking conditions...")

    while ((l[0] == h[0]) or (l[1] == '1' and h[1] == '0')) is True:
        if l[0] == h[0]:
            l = l[1:] + '0'
            h = h[1:] + '1'
            t_bin = t_bin[1:] + rem_tag[0]
            rem_tag = rem_tag[1:]
            print("  i. e1/e2 condition: low = {}, high = {}, tag = {}".format(l, h, t_bin))

        if l[1] == '1' and h[1] == '0':
            l = '0' + l[2:] + '0'
            h = '1' + h[2:] + '1'

            t_bin = t_bin[1:] + rem_tag[0]
            rem_tag = rem_tag[1:]
            complement = '0' if t_bin[0] == '1' else '1'
            t_bin = complement + t_bin[1:]
            print("  ii. e3 condition: low = {}, high = {}, tag = {}".format(l, h, t_bin))

    print(" f. Final updated binary values: l = {}, h = {}, tag = {}".format(l, h, t_bin), end='\n\n')
    return l, h, t_bin, rem_tag


max_char = 128
# table_vals = {chr(v): v+1 for v in range(128)}
# table = {'': 0}
# table.update(table_vals)
# print("char table:", table, end='\n\n')

file = sys.argv[1]
file_name, extension = os.path.splitext(file)
print("File name: ", file_name)

# change to .tex in final implementation
if extension != ".lz":
    print("Not a compatible compressed file!")
    exit(1)

with open(file, 'rb') as f:
    remaining_tag = pickle.load(f)

m = 8
current_tag = remaining_tag[:m]
remaining_tag = remaining_tag[m:]

outputs = []
low = '0' * m
high = '1' * m
sequence = ""
length = 13

for count in range(length):
    print("\n   DECODING SYMBOL INDEXED {}".format(count))

    low_prob, high_prob, symbol = find_bounds(current_tag, low, high, max_char)

    low, high, current_tag, remaining_tag = update_lh(t_bin=current_tag, rem_tag=remaining_tag,
                                                      l_bin=low, h_bin=high,
                                                      l_prob=low_prob, h_prob=high_prob)

    sequence += chr(symbol)

for char in sequence:
    print(repr(char), end='')
