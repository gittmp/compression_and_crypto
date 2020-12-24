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
    print("File: ", file)

    if file.mode != 'r':
        print("Error")
        exit()

    file_contents = file.read()
    print("File contents:")
    print(file_contents)

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


def arithmetic_decoder(m, t_bin, it, l_bin, h_bin, l_prob, h_prob):
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


def init_decoding(t_bin, input_tag, l_bin, h_bin, m):
    initial_symbols = []

    for i in range(N):
        tg = int(t_bin, 2)
        l = int(l_bin, 2)
        h = int(h_bin, 2)
        symbol = None

        freq_val = math.floor(((tg - l + 1) * 128 - 1) / (h - l + 1))
        p = freq_val / 128
        print("\nSearch: freq = {}, p = {}".format(freq_val, p))

        for j in range(128):
            low_bound = j * (1 / 128)
            high_bound = (j + 1) * (1 / 128)
            print("Interval: {} -> {}".format(low_bound, high_bound))

            if low_bound <= p < high_bound:
                symbol = chr(j)
                print("Found:", symbol)
                l, h, t_bin, input_tag = arithmetic_decoder(m, t_bin, input_tag, l_bin, h_bin, low_bound, high_bound)
                break

        initial_symbols.append(symbol)

    return initial_symbols, l_bin, h_bin, t_bin, input_tag


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

sequence, low, high, t, tag = init_decoding(t, tag, low, high, m)

print("Start of sequence = ", sequence)
print("Low = {}, High = {}, Current tag = {}".format(low, high, t))
