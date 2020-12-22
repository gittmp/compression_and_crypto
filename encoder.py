# Usage: python encoder.py myfile.tex
# encodes a lossless compression of a LaTeX file
"""
import sys
import os

file_name = sys.argv[1]

name, extension = os.path.splitext(file_name)
print("File name: ", name)
print("File extension: ", extension)

if extension != ".txt":
    print("Not a LaTeX file!")
    exit()

file = open(file_name, 'r')
print("File: ", file)

if file.mode == 'r':
    file_contents = file.read()
    print("File contents: ", file_contents)
"""
import math


# METHOD B: esc count = no. distinct symbols in context dict
# & each symbol's count starts from the 2nd observation
def ppm_step_b(symbol, n, context, exclusion_list):
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
    out = {"symbol": symbol, "l_prob": 0.0, "h_prob": 1/size}
    return out


def arithmetic_encoder(l_old, h_old, e3_count, m, ppm_output):
    symbol = ppm_output["symbol"]
    l_prob = ppm_output["l_prob"]
    h_prob = ppm_output["h_prob"]
    out = ''

    l_old = int(l_old, 2)
    h_old = int(h_old, 2)

    l_new = l_old + math.floor((h_old - l_old + 1) * l_prob)
    h_new = l_old + math.floor((h_old - l_old + 1) * h_prob) - 1

    # print("new l,h ints calculated:", l_new, h_new)

    l_new = format(l_new, 'b')
    l = l_new + '0' * (m - len(l_new))
    h_new = format(h_new, 'b')
    h = h_new + '1' * (m - len(h_new))

    # print("new l,h values calculated:", l, h)

    e1e2_condition = (l[0] == h[0])
    e3_condition = (l[0] != h[0] and l[1] == '1' and h[1] == '0')

    while (e1e2_condition or e3_condition) is True:
        if e1e2_condition:
            e3_bit = '0' if l[0] == '1' else '1'
            out += l[0] + e3_bit * e3_count
            e3_count = 0

            l = l[1:] + '0'
            h = h[1:] + '1'
            # print("MSBs are both", l[0], " --> shifting out bits:", l, h)

        elif e3_condition:
            l = '0' + l[2:] + '0'
            h = '1' + h[2:] + '1'
            e3_count += 1
            # print("e3 condition met --> incrementing counter:", e3_count)

        e1e2_condition = (l[0] == h[0])
        e3_condition = ((l[0] != h[0]) and l[1] == '1' and h[1] == '0')

    # return l, h, e3_count, out
    return {
        "l": l,
        "h": h,
        "e3": e3_count,
        "output": out
    }


def terminate_encoding(l, e3):
    if e3 > 0:
        msb = l[0]
        e3_bit = '0' if msb == '1' else '1'
        out = msb + e3_bit * e3 + l[1:]
    else:
        out = l

    return out


sequence = "this is the tithe"
alphabet_size = 7
print("Sequence to encode:", sequence, end='\n\n')

N = 4
sequence = "-" * N + sequence
D = [{} for i in range(N + 1)]
outputs = []
codewords = []
m = 2 + math.ceil(math.log2(len(sequence)))
low = '0' * m
high = '1' * m
e3_counter = 0


for i in range(N, len(sequence)):
    n = N
    symb = sequence[i]
    excluded = []
    symbol_outputs = []
    code = ''

    while n > -2:
        context = sequence[i-n:i]

        if n > -1:
            output, excluded = ppm_step_b(symb, n, context, excluded)
        else:  # n == -1
            output = order_minus1(symb, alphabet_size)

        symbol_outputs.append(output)

        encoding = arithmetic_encoder(low, high, e3_counter, m, output)
        low = encoding["l"]
        high = encoding["h"]
        e3_counter = encoding["e3"]
        code += encoding["output"]

        if output["symbol"] == symb:
            if code != '':
                codewords.append(code)
            outputs.append(symbol_outputs)
            break
        else:
            n -= 1
            
terminal_code = terminate_encoding(low, e3_counter)
codewords.append(terminal_code)

print("D =")
for i in range(N+1):
    print(D[i])

print("\n\nOUTPUTS =")
for i in range(len(outputs)):
    print(outputs[i])

print("\n\nENCODING =")
for i in range(len(codewords)):
    print(codewords[i])

