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

    m = int(file_contents[:8], 'b')
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


def order_minus1(symbol, size):

    if symbol in initial_dist:
        index = initial_dist.index(symbol)
    else:
        index = len(initial_dist)
        initial_dist.append(symbol)

    p = index * (1 / size)
    prev_p = (index - 1) * (1 / size)
    out = {"symbol": symbol, "l_prob": prev_p, "h_prob": p}

    return out


def init_decode_symbol(tg, l, h, size):
    tg = int(t, 'b')
    l = int(l, 'b')
    h = int(h, 'b')

    freq_val = math.floor(((tg - l + 1) * size - 1) / (h - l + 1))


file, m, tag = get_file_input()
t = tag[:m]
alphabet_size = 7
print("Sequence to decode:", tag, end='\n\n')

N = 4
D = [{} for i in range(N + 1)]
initial_dist = []
outputs = []
low = '0' * m
high = '1' * m
e3_counter = 0


