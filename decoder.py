# Usage: python decoder.py myfile.lz

import os
import sys
import math
import ast


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

    index = file_contents.index(']')
    distribution = file_contents[:index + 1]
    distribution = ast.literal_eval(distribution)
    m = int(file_contents[index + 1:index + 9], 2)
    tag = file_contents[index + 9:]

    return name, distribution, m, tag


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
        index = max(1.0, initial_dist.index(symbol))
    else:
        index = max(1.0, len(initial_dist))
        initial_dist.append(symbol)

    p = index * (1 / size)
    prev_p = (index - 1) * (1 / size)
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
            t_bin[0] = '0' if it[0] == '1' else '1'

        e1e2_condition = (l[0] == h[0])
        e3_condition = ((l[0] != h[0]) and l[1] == '1' and h[1] == '0')

    return l, h, t_bin, it


def init_decoding(t_bin, input_tag, l_bin, h_bin, m, size):
    initial_symbols = []

    for i in range(N):
        tg = int(t_bin, 2)
        l = int(l_bin, 2)
        h = int(h_bin, 2)
        symbol = None

        freq_val = math.floor(((tg - l + 1) * size - 1) / (h - l + 1))
        p = freq_val / size
        low_bound = 0
        for j in range(1, len(initial_dist)):
            prev_index = j - 1
            index = j
            low_bound += prev_index * (1 / size)
            high_bound = index * (1 / size)

            if low_bound <= p < high_bound:
                symbol = initial_dist[j]
                l, h, t_bin, input_tag = arithmetic_decoder(m, t_bin, input_tag, l_bin, h_bin, low_bound, high_bound)
                break

        initial_symbols.append(symbol)

    return initial_symbols, l_bin, h_bin, t_bin, input_tag


file, initial_dist, m, tag = get_file_input()
t = tag[:m]
tag = tag[m:]
alphabet_size = 7
print("order -1 distribution:", initial_dist)
print("m:", m)
print("Sequence to decode:", tag, end='\n\n')

N = 4
D = [{} for i in range(N + 1)]
outputs = []
low = '0' * m
high = '1' * m
e3_counter = 0


