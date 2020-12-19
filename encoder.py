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

sequence = "--ABABACCA"
alphabet_size = 3

N = 2
D = [{"esc": 1},
     {},
     {}]
encodings = []
outputs = []


def ppm_step(symbol, n, context, exclusion_list):
    if n > 0:
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
            out = {"symbol": "esc", "probability": 1}
    else:  # n == 0
        if symbol in D[n].keys():
            p = D[n][symbol] / sum([D[n][k] for k in D[n].keys() if k not in exclusion_list])
            D[n][symbol] += 1
            out = {"symbol": symbol, "probability": p}
        else:
            p = D[n]["esc"] / sum([D[n][k] for k in D[n].keys() if k not in exclusion_list])
            D[n][symbol] = 1
            out = {"symbol": "esc", "probability": p}

    print("output = ", out)
    print("exclusion list = ", exclusion_list)

    return out, exclusion_list


def order_minus1(symbol):
    out = {"symbol": symbol, "probability": 1/alphabet_size}
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
            output, excluded = ppm_step(symb, n, context, excluded)
        else:  # n == -1
            output = order_minus1(symb)

        outputs.append(output)
        encoded_symbol = arithmetic_encoder(output)

        if output["symbol"] == symb:
            break
        else:
            n -= 1

print("\nOUTPUTS =", outputs)
print("D = ")
for m in range(N+1):
    print(D[m])
