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

sequence = "ALOMOHORA_AHOROMOLA_AROHOMOLA_ALOHOMOR"
alphabet_size = 7

print("Sequence to encode:", sequence, end='\n\n')

N = 4
sequence = "-"*N + sequence
D = [{} for i in range(N+1)]
encodings = []
outputs = []


# METHOD B: esc count = no. distinct symbols in context dict
# & each symbol's count starts from the 2nd observation
def ppm_step_b(symbol, n, context, exclusion_list):
    if context in D[n].keys():
        if symbol in D[n][context].keys():
            if D[n][context][symbol] != 0:
                sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
                print("context row a =", D[n][context])

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
                print("context row b =", D[n][context])

                if sum_values == 0:
                    p = 1.0
                else:
                    p = D[n][context]["esc"] / sum_values

                D[n][context]["esc"] += 1
                out = {"symbol": "esc", "l_prob": 0.0, "h_prob": p}

            D[n][context][symbol] += 1
        else:
            sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
            print("context row c =", D[n][context])

            if sum_values == 0:
                p = 1.0
            else:
                p = D[n][context]["esc"] / sum_values

            exclusion_list.extend([k for k in D[n][context].keys() if k != "esc" and k not in exclusion_list])

            D[n][context][symbol] = 0
            out = {"symbol": "esc", "l_prob": 0.0, "h_prob": p}
    else:
        D[n][context] = {"esc": 0, symbol: 0}
        print("context row d =", D[n][context])
        out = {"symbol": "esc", "l_prob": 0.0, "h_prob": 1.0}

    if len(exclusion_list) > 0:
        print("exclusion list = ", exclusion_list)
    print("output = ", out)

    return out, exclusion_list


def order_minus1(symbol, size):
    out = {"symbol": symbol, "l_prob": 0.0, "h_prob": 1/size}
    return out


def init_lh(sequence_length):
    m = 2 + math.ceil(math.log2(sequence_length))
    l = '0'*m
    h = '1'*m
    return l, h


def arithmetic_encoder(ppm_output):
    return "encoded"


for i in range(N, len(sequence)):
    n = N
    symb = sequence[i]
    excluded = []
    while n > -2:
        context = sequence[i-n:i]
        # print("symbol=", symb, " n=", n, " context=", context)

        if n > -1:
            output, excluded = ppm_step_b(symb, n, context, excluded)
        else:  # n == -1
            output = order_minus1(symb, alphabet_size)

        outputs.append(output)
        encoded_symbol = arithmetic_encoder(output)

        if output["symbol"] == symb:
            break
        else:
            n -= 1
    print()

# print("D =")
# for i in range(N+1):
#     print(D[i])
#
# print("\n\nOUTPUTS =")
# for i in range(len(outputs)):
#     print(outputs[i])

