import os
import sys
import math


def get_file_input():
    file_name = sys.argv[1]
    name, extension = os.path.splitext(file_name)
    print("File name: ", name)

    # change to .tex in final implementation
    if extension != ".lz":
        print("Not a compatible compressed file!")
        exit()

    file = open(file_name, 'r')

    if file.mode != 'r':
        print("Error")
        exit()

    tag = file.read()

    return name, tag


def update_lh(t_bin, rem_tag, l_bin, h_bin, l_prob, h_prob):
    l_old = int(l_bin, 2)
    h_old = int(h_bin, 2)

    l_new = l_old + math.floor((h_old - l_old + 1) * l_prob)
    h_new = l_old + math.floor((h_old - l_old + 1) * h_prob) - 1

    print("low prob = {}, high prob = {}".format(l_prob, h_prob))
    print("int l_old -> l_new: {} -> {}".format(l_old, l_new))
    print("int h_old -> h_new: {} -> {}".format(h_old, h_new))

    l_new = format(l_new, 'b')
    l = l_new + '0' * (m - len(l_new))
    h_new = format(h_new, 'b')
    h = h_new + '1' * (m - len(h_new))

    print("binary versions: l = {}, h = {}".format(l_new, h_new))

    while ((l[0] == h[0]) or (l[1] == '1' and h[1] == '0')) is True:
        if l[0] == h[0]:
            l = l[1:] + '0'
            h = h[1:] + '1'
            t_bin = t_bin[1:] + rem_tag[0]
            rem_tag = rem_tag[1:]
            print("e1/e2 condition: low = {}, high = {}, tag = {}".format(l, h, t_bin))

        if l[1] == '1' and h[1] == '0':
            l = '0' + l[2:] + '0'
            h = '1' + h[2:] + '1'

            t_bin = t_bin[1:] + rem_tag[0]
            rem_tag = rem_tag[1:]
            complement = '0' if t_bin[0] == '1' else '1'
            t_bin = complement + t_bin[1:]
            print("e3 condition: low = {}, high = {}, tag = {}".format(l, h, t_bin))

    print("Final updated binary values: l = {}, h = {}, tag = {}".format(l, h, t_bin), end='\n\n')
    return l, h, t_bin, rem_tag


def find_bounds(t_bin, l_bin, h_bin, total):
    tg = int(t_bin, 2)
    l = int(l_bin, 2)
    h = int(h_bin, 2)
    low_bound, high_bound = 0, 0

    print(" a. inputs: tag = {} -> {}, low = {} -> {}, high = {} -> {}".format(t_bin, tg, l_bin, l, h_bin, h))

    # find frequency value
    frequency = math.floor(((tg - l + 1) * total - 1) / (h - l + 1))

    print(" b. decoded frequency = {}".format(frequency))

    # this is where you check what interval correlated to p
    keys = list(table.keys())
    j = 0

    while frequency >= high_bound:
        j += 1
        low_bound = high_bound
        high_bound = table[keys[j]]

    symb = keys[j]

    # while frequency >= high_bound:
    #     high_bound += 1
    #
    # low_bound = high_bound - 1
    # symb = chr(low_bound)

    print(" c. found symbol = {}, interval = [{}/{}, {}/{})".format(symb, low_bound, total, high_bound, total))

    low_bound = low_bound / total
    high_bound = high_bound / total

    return low_bound, high_bound, str(symb)


file, remaining_tag = get_file_input()
print("Sequence to decode:", remaining_tag)

no_chars = 128
table_vals = {chr(v): v+1 for v in range(128)}
table = {'': 0}
table.update(table_vals)
print("char table:", table, end='\n\n')

m = 8
current_tag = remaining_tag[:m]
remaining_tag = remaining_tag[m:]

outputs = []
low = '0' * m
high = '1' * m
sequence = ""

for count in range(53):
    print("\n   DECODING SYMBOL INDEX {}".format(count))

    low_prob, high_prob, symbol = find_bounds(current_tag, low, high, no_chars)

    low, high, current_tag, remaining_tag = update_lh(t_bin=current_tag, rem_tag=remaining_tag,
                                                      l_bin=low, h_bin=high,
                                                      l_prob=low_prob, h_prob=high_prob)

    tag_length = len(remaining_tag)
    sequence += symbol

    print("Low = {}, High {}, Tag = {}".format(low, high, current_tag))

print("sequence =", sequence)
