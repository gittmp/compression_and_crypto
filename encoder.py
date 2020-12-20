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

sequence = "ABABACCA"
alphabet_size = 3

N = 2
sequence = "-"*N + sequence
D = [{} for i in range(N+1)]
encodings = []
outputs = []


# METHOD A: esc count = 1
def ppm_step_a(symbol, n, context, exclusion_list):
    if context in D[n].keys():
        if symbol in D[n][context].keys():
            p = D[n][context][symbol] / sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
            D[n][context][symbol] += 1
            out = {"symbol": symbol, "probability": p}
        else:
            p = D[n][context]["esc"] / sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
            exclusion_list.extend([k for k in D[n][context].keys() if k != "esc" and k not in exclusion_list])
            D[n][context][symbol] = 1
            out = {"symbol": "esc", "probability": p}
    else:
        D[n][context] = {"esc": 1, symbol: 1}
        out = {"symbol": "esc", "probability": 1.0}

    print("output = ", out)
    print("exclusion list = ", exclusion_list)

    return out, exclusion_list


# METHOD C: esc count = no. distinct symbols in context dict
def ppm_step_c(symbol, n, context, exclusion_list):
    if context in D[n].keys():
        if symbol in D[n][context].keys():
            p = D[n][context][symbol] / sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
            D[n][context][symbol] += 1
            out = {"symbol": symbol, "probability": p}
        else:
            p = D[n][context]["esc"] / sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
            exclusion_list.extend([k for k in D[n][context].keys() if k != "esc" and k not in exclusion_list])
            D[n][context][symbol] = 1
            D[n][context]["esc"] += 1
            out = {"symbol": "esc", "probability": p}
    else:
        D[n][context] = {"esc": 1, symbol: 1}
        out = {"symbol": "esc", "probability": 1.0}

    print("output = ", out)
    print("exclusion list = ", exclusion_list)

    return out, exclusion_list


# METHOD B: esc count = no. distinct symbols in context dict
# & each symbol's count starts from the 2nd observation
def ppm_step_b(symbol, n, context, exclusion_list):
    if context in D[n].keys():
        if symbol in D[n][context].keys():
            if D[n][context][symbol] != 0:
                sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
                if sum_values == 0:
                    p = 1.0
                else:
                    p = D[n][context][symbol] / sum_values
                out = {"symbol": symbol, "probability": p}
            else:
                # if the symbol exists but is zero don't count it as there as count only starts on 2nd observation
                sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
                if sum_values == 0:
                    p = 1.0
                else:
                    p = D[n][context]["esc"] / sum_values

                D[n][context]["esc"] += 1
                out = {"symbol": "esc", "probability": p}

            D[n][context][symbol] += 1
        else:
            sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
            if sum_values == 0:
                p = 1.0
            else:
                p = D[n][context]["esc"] / sum_values
            exclusion_list.extend([k for k in D[n][context].keys() if k != "esc" and k not in exclusion_list])
            D[n][context][symbol] = 0
            out = {"symbol": "esc", "probability": p}
    else:
        D[n][context] = {"esc": 0, symbol: 0}
        out = {"symbol": "esc", "probability": 1.0}

    print("output = ", out)
    print("exclusion list = ", exclusion_list)

    return out, exclusion_list


def order_minus1(symbol, size):
    out = {"symbol": symbol, "probability": 1/size}
    return out


def arithmetic_encoder(ppm_output):
    return "encoded"


for i in range(N, len(sequence)):
    n = N
    symb = sequence[i]
    excluded = []
    while n > -2:
        context = sequence[i-n:i]
        print("symbol=", symb, " n=", n, " context=", context)

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

print("D =")
for m in range(N+1):
    print(D[m])

print("\n\nOUTPUTS =")
for i in range(len(outputs)):
    print(outputs[i])

