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

sequence = "--" + sequence
N = 2
D = [{},
     {},
     {}]
encodings = []
outputs = []


def ppm_step(symbol, n, context, exclusion_list):
    if context in D[n].keys():
        if symbol in D[n][context].keys():
            p = D[n][context][symbol] / sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
            D[n][context][symbol] += 1
            out = {"symbol": symbol, "probability": round(p, 4)}
        else:
            p = D[n][context]["esc"] / sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
            exclusion_list.extend([k for k in D[n][context].keys() if k != "esc" and k not in exclusion_list])
            D[n][context][symbol] = 1
            out = {"symbol": "esc", "probability": round(p, 4)}
    else:
        D[n][context] = {"esc": 1, symbol: 1}
        out = {"symbol": "esc", "probability": 1.0}

    print("output = ", out)
    print("exclusion list = ", exclusion_list)

    return out, exclusion_list


def order_minus1(symbol):
    out = {"symbol": symbol, "probability": round(1/alphabet_size, 4)}
    return out


def arithmetic_encoder(ppm_output):
    return "encoded"


for i in range(N, len(sequence)):
    n = N
    symb = sequence[i]
    excluded = []
    print()
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

print("D =")
for m in range(N+1):
    print(D[m])

print("\n\nOUTPUTS =")
for i in range(len(outputs)):
    print(outputs[i])

