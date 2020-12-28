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

    file_contents = file.read()
    m = int(file_contents[:8], 2)
    tag = file_contents[8:]

    return name, m, tag


# PPM METHOD B: esc count = no. distinct symbols in context dict
# & each symbol's count starts from the 2nd observation
def ppm_step(symbol, n, context, exclusion_list):
    if context in D[n].keys():
        if symbol in D[n][context].keys():
            if D[n][context][symbol] != 0:
                sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
                p = D[n][context][symbol] / sum_values

                keys = list(D[n][context].keys())
                symb_index = keys.index(symbol)
                cum_prev_f = 0
                for i in range(symb_index):
                    key = keys[i]
                    if key not in exclusion_list:
                        cum_prev_f += D[n][context][key]

                prev_p = cum_prev_f / sum_values
                out = {"symbol": symbol, "l_prob": prev_p, "h_prob": prev_p + p}
            else:
                # if the symbol exists but is zero don't count it as there as count only starts on 2nd observation
                sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])

                if sum_values == 0:
                    p = 1.0
                else:
                    p = D[n][context]["esc"] / sum_values

                D[n][context]["esc"] += 1
                out = {"symbol": "esc", "l_prob": 0.0, "h_prob": p}

            D[n][context][symbol] += 1
        else:
            sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])

            if sum_values == 0:
                p = 1.0
            else:
                p = D[n][context]["esc"] / sum_values

            exclusion_list.extend([k for k in D[n][context].keys() if k != "esc" and k not in exclusion_list])

            D[n][context][symbol] = 0
            out = {"symbol": "esc", "l_prob": 0.0, "h_prob": p}
    else:
        D[n][context] = {"esc": 0, symbol: 0}
        out = {"symbol": "esc", "l_prob": 0.0, "h_prob": 1.0}

    return out, exclusion_list


def order_minus1(symbol):

    char_code = ord(symbol)
    prev_p = char_code * (1 / 128)
    p = (char_code + 1) * (1 / 128)

    out = {"symbol": symbol, "l_prob": prev_p, "h_prob": p}

    return out


def update_lh(m, t_bin, it, l_bin, h_bin, l_prob, h_prob):
    l_old = int(l_bin, 2)
    h_old = int(h_bin, 2)

    l_new = l_old + math.floor((h_old - l_old + 1) * l_prob)
    h_new = l_old + math.floor((h_old - l_old + 1) * h_prob) - 1

    l_new = format(l_new, 'b')
    l = l_new + '0' * (m - len(l_new))
    h_new = format(h_new, 'b')
    h = h_new + '1' * (m - len(h_new))

    e1e2_condition = (l[0] == h[0])
    e3_condition = (l[0] != h[0] and l[1] == '1' and h[1] == '0')

    while (e1e2_condition or e3_condition) is True:
        if e1e2_condition:
            l = l[1:] + '0'
            h = h[1:] + '1'
            t_bin = t_bin[1:] + it[0]
            it = it[1:]

        elif e3_condition:
            l = '0' + l[2:] + '0'
            h = '1' + h[2:] + '1'

            t_bin = t_bin[1:] + it[0]
            it = it[1:]
            complement = '0' if t_bin[0] == '1' else '1'
            t_bin = complement + t_bin[1:]

        e1e2_condition = (l[0] == h[0])
        e3_condition = ((l[0] != h[0]) and l[1] == '1' and h[1] == '0')

    return l, h, t_bin, it


def ppm_decoding(t_bin, input_tag, l_bin, h_bin, m):
    initial_symbols = []

    for i in range(N):
        tg = int(t_bin, 2)
        l = int(l_bin, 2)
        h = int(h_bin, 2)
        symbol = None
        low_bound = 0
        high_bound = 1

        # here calculating p is what needs to utilise ppm
        # the 128 comes from the order -1 distribution, i.e. all 128 symbols, but may need to adapt to which order
        freq_val = math.floor(((tg - l + 1) * 128 - 1) / (h - l + 1))

        p = freq_val / 128
        print("p = {}".format(p))

        # p2 = (tg - l) / (h - l)
        # print("p2 = {}".format(p2))

        # this is where you check what interval correlated to p (in order -1)
        for j in range(128):
            low_bound = j * (1 / 128)
            high_bound = (j + 1) * (1 / 128)

            if low_bound <= p < high_bound:
                symbol = chr(j)
                break

        initial_symbols.append(symbol)

        # update low and high bounds
        l, h, t_bin, input_tag = update_lh(m, t_bin, input_tag, l_bin, h_bin, low_bound, high_bound)
        print("l = {}, h = {}".format(l, h))

    return initial_symbols, l_bin, h_bin, t_bin, input_tag


def backtrack_update(i, decoded_sequence, n, symbol):
    while n <= N:
        # find nth order context
        context = decoded_sequence[i - n:]

        # update count of context-symbol in D
        if context in D[n].keys():
            if symbol in D[n][context].keys():
                if D[n][context][symbol] == 0:
                    # if the symbol exists but is zero increment esc count (method B) as well as symbol count
                    D[n][context]["esc"] += 1
                D[n][context][symbol] += 1
            else:
                D[n][context][symbol] = 0
        else:
            D[n][context] = {"esc": 0, symbol: 0}

        # increment n
        n += 1


def symbol_search(context, n, tg, init_tag, l, h, exclusion_list, i, decoded_sequence):
    # search order n for context
    if context in D[n].keys():
        # if context found, check if there are any non-zero counts
        sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
        if sum_values > 0:
            # calculate freq_val then p based upon counts in this section
            freq_val = math.floor(((tg - l + 1) * sum_values - 1) / (h - l + 1))
            p = freq_val / sum_values

            # find symbol corresponding to the interval p falls within
            keys = D[n][context].keys()
            low_bound = 0
            high_bound = 0
            symbol = "esc"
            for key in keys:
                if key not in exclusion_list:
                    high_bound += D[n][context][keys] / sum_values
                    if low_bound <= p < high_bound:
                        symbol = key
                        print("found symbol =", symbol)
                        break
                    else:
                        low_bound = high_bound

            # if found symbol is the escape symbol, update l and h and decrement n
            if symbol == "esc":
                new_lht = update_lh(m, tg, init_tag, l, h, l_prob=low_bound, h_prob=high_bound)
                n -= 1
                exclusion_list.extend([k for k in keys if k != "esc"])
                out = {'n': n, "lht_update": new_lht, "found": False, "symbol": "esc"}
            # otherwise we've found the symbol
            else:
                # output symbol, update l and h and backtrack through orders n -> N updating context-symbol counts
                new_lht = update_lh(m, tg, init_tag, l, h, l_prob=low_bound, h_prob=high_bound)
                backtrack_update(i, decoded_sequence, n, symbol)
                out = {'n': n, "lht_update": new_lht, "found": True, "symbol": symbol}
        # otherwise, if no non-zero elements corresponding to context
        else:
            # update l and h and decrement n
            new_lht = update_lh(m, tg, init_tag, l, h, l_prob=0.0, h_prob=1.0)
            n -= 1
            out = {'n': n, "lht_update": new_lht, "found": False, "symbol": "esc"}
    # otherwise, if context not in D
    else:
        # update l and h and decrement n
        new_lht = update_lh(m, tg, init_tag, l, h, l_prob=0.0, h_prob=1.0)
        n -= 1
        out = {'n': n, "lht_update": new_lht, "found": False, "symbol": "esc"}

    return out


file, m, tag = get_file_input()
t = tag[:m]
tag = tag[m:]
print("m:", m)
print("Sequence to decode:", tag, end='\n\n')

N = 4
D = [{} for i in range(N + 1)]
outputs = []
low = '0' * m
high = '1' * m

sequence, low, high, t, tag = ppm_decoding(t, tag, low, high, m)

print("Start of sequence = ", sequence)
print("Low = {}, High = {}, Current tag = {}".format(low, high, t))
