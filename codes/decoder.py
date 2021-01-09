# Usage: python decoder.py myfile.lz

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


def update_lh(m, t_bin, rem_tag, l_bin, h_bin, l_prob, h_prob):
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
        if l[1] == '1' and h[1] == '0':
            print("e3 condition")
            l = '0' + l[2:] + '0'
            h = '1' + h[2:] + '1'

            t_bin = t_bin[1:] + rem_tag[0]
            rem_tag = rem_tag[1:]
            complement = '0' if t_bin[0] == '1' else '1'
            t_bin = complement + t_bin[1:]

        if l[0] == h[0]:
            print("e1/e2 condition")
            l = l[1:] + '0'
            h = h[1:] + '1'
            t_bin = t_bin[1:] + rem_tag[0]
            rem_tag = rem_tag[1:]

    print("Final updated binary values: l = {}, h = {}, tag = {}".format(l, h, t_bin), end='\n\n')
    return l, h, t_bin, rem_tag


def backtrack_update(i, decoded_sequence, n, symb):
    while n <= N:
        # find nth order context
        c = decoded_sequence[i - n:]
        # print("Updating D with: n = {}, i = {}, context = {}, symbol = {}".format(n, i, c, symb))

        # update count of context-symbol in D
        if c in D[n].keys():
            if symb in D[n][c].keys():
                if D[n][c][symb] == 0:
                    # if the symbol exists but is zero increment esc count (method B) as well as symbol count
                    D[n][c]["esc"] += 1
                D[n][c][symb] += 1
            else:
                esc_count = D[n][c].pop("esc", 0)
                D[n][c][symb] = 0
                D[n][c]["esc"] = esc_count
        else:
            D[n][c] = {symb: 0, "esc": 0}

        # increment n
        n += 1


def find_bounds(t_bin, l_bin, h_bin, total, n, c):
    tg = int(t_bin, 2)
    l = int(l_bin, 2)
    h = int(h_bin, 2)
    symb = None
    low_bound, high_bound = 0, 1

    print(" a. inputs: tag = {} -> {}, low = {} -> {}, high = {} -> {}".format(t_bin, tg, l_bin, l, h_bin, h))

    # find frequency value
    frequency = math.floor(((tg - l + 1) * total - 1) / (h - l + 1))

    print(" b. decoded frequency = {}".format(frequency))

    # this is where you check what interval correlated to p (in order -1)
    if n == -1:

        while frequency >= high_bound:
            high_bound += 1

        low_bound = high_bound - 1
        symb = chr(low_bound)

        print(" c. using order -1, found symbol = {}, interval = [{}/{}, {}/{})".format(symb, low_bound, total, high_bound, total))
    else:
        # find symbol corresponding to the interval p falls within
        keys = list(D[n][c].keys())
        j = 0
        high_bound = D[n][c][keys[j]]
        while frequency >= high_bound:
            j += 1
            low_bound = high_bound
            high_bound += D[n][c][keys[j]]

        symb = keys[j]

        print(" c. using higher order: {} <= {} < {}, found symbol = {}, interval = [{}, {}) = [{}, {})".format(low_bound, frequency, high_bound, symb, low_bound, high_bound, low_bound/total, high_bound/total))

    low_bound = low_bound / total
    high_bound = high_bound / total

    return low_bound, high_bound, symb


def symbol_search(c, n, tg_bin, i, l_bin, h_bin, exclusion_list, decoded_sequence):

    # search order n for context
    if c in D[n].keys():
        # if context found, check if there are any non-zero counts
        print("1) context in D with symbols: D[{}]['{}'] = {}".format(n, context, D[n][context]))

        sum_values = sum([D[n][c][k] for k in D[n][c].keys() if k not in exclusion_list])

        if sum_values > 0:

            low_bound, high_bound, symb = find_bounds(t_bin=tg_bin, l_bin=l_bin, h_bin=h_bin,
                                                      total=sum_values, n=n, c=c)

            print("2) sum of values > 0: sum = {}, found bound = [{}, {}), symbol = {}".format(sum_values, low_bound, high_bound, symb))

            # if found symbol is the escape symbol, update l and h and decrement n
            if symb == "esc":
                keys = D[n][c].keys()
                exclusion_list.extend([k for k in keys if k != "esc"])

                out = {"low": low_bound, "high": high_bound, "excl": exclusion_list, "found": False, "symbol": "esc"}
            # otherwise we've found the symbol
            else:
                # output symbol, update l and h and backtrack through orders n -> N updating context-symbol counts
                print("3) correct symbol found, perform backtrack update")
                backtrack_update(i, decoded_sequence, n, symb)

                out = {"low": low_bound, "high": high_bound, "excl": exclusion_list, "found": True, "symbol": symb}
        # otherwise, if no non-zero elements corresponding to context
        else:
            # this bit works fine
            print("4) all symbols zero, escape: symbol = 'esc', prob bound = [0.0, 1.0)")

            out = {"low": 0.0, "high": 1.0, "excl": exclusion_list, "found": False, "symbol": "esc"}
    # otherwise, if context not in D
    else:
        # this bit works fine
        print("5) context never observed, escape: symbol = 'esc', prob bound = [0.0, 1.0)")

        out = {"low": 0.0, "high": 1.0, "excl": exclusion_list, "found": False, "symbol": "esc"}

    return out


file, remaining_tag = get_file_input()

m = 9
current_tag = remaining_tag[:m]
remaining_tag = remaining_tag[m:]
# print("m:", m)
# print("Sequence to decode:", tag, end='\n\n')

N = 4
D = [{} for i in range(N + 1)]
outputs = []
low = '0' * m
high = '1' * m

sequence = "----"
tag_length = len(remaining_tag)

# while tag_length > 0:
for count in range(N, 13):
    # print("\n\nCOUNT={}\n".format(count))
    output = None
    order = N
    excluded = []
    print("\n   DECODING SYMBOL {}".format(count))

    while order > -2:
        if order > -1:
            context = sequence[count-order:]
            print("\nSEARCHING ORDER {}, CONTEXT = {}".format(order, context))

            output = symbol_search(context, order, tg_bin=current_tag,
                                   i=count, l_bin=low, h_bin=high,
                                   exclusion_list=excluded, decoded_sequence=sequence)

            low_prob = output["low"]
            high_prob = output["high"]

            if not (low_prob == 0.0 and high_prob == 1.0):
                low, high, current_tag, remaining_tag = update_lh(m=m,
                                                                  t_bin=current_tag, rem_tag=remaining_tag,
                                                                  l_bin=low, h_bin=high,
                                                                  l_prob=low_prob, h_prob=high_prob)

            excluded = output["excl"]
            tag_length = len(remaining_tag)

            if output["found"]:
                # print("FOUND CHAR = {}".format(output["symbol"]))
                sequence += output["symbol"]
                break
            else:
                # print("ESCAPE ORDER {}".format(order))
                order -= 1
        else:
            print("\nUSING ORDER -1")

            low_prob, high_prob, symbol = find_bounds(t_bin=current_tag, l_bin=low, h_bin=high,
                                                      total=128, n=order, c=None)

            # update counts for all orders in D
            backtrack_update(i=count, decoded_sequence=sequence, n=0, symb=symbol)

            low, high, current_tag, remaining_tag = update_lh(m=m,
                                                              t_bin=current_tag, rem_tag=remaining_tag,
                                                              l_bin=low, h_bin=high,
                                                              l_prob=low_prob, h_prob=high_prob)

            tag_length = len(remaining_tag)
            sequence += symbol

            print("Low = {}, High {}, Tag = {}".format(low, high, current_tag))

            break

print("sequence =", sequence)

