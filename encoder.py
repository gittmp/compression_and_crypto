# Usage: python encoder.py myfile.tex
# encodes a lossless compression of a LaTeX file
import sys
import os
import math


def get_file_input():
    file_name = sys.argv[1]
    name, extension = os.path.splitext(file_name)
    print("File name: ", name)

    # change to .tex in final implementation
    if extension != ".txt":
        print("Not a LaTeX file!")
        exit()

    f = open(file_name, 'r')
    print("File: ", f)

    if f.mode != 'r':
        print("Error")
        exit()

    file_contents = f.read()

    return file_contents, name


def output_file(encoded_seq, file_name):
    f = open(file_name + ".lz", "w")
    encoded_seq = str(encoded_seq)
    f.write(encoded_seq)
    f.close()


# PPM METHOD B: esc count = no. distinct symbols in context dict
# & each symbol's count starts from the 2nd observation
def ppm_step(symbol, n, context, exclusion_list):
    if context in D[n].keys():
        sum_values = sum([D[n][context][k] for k in D[n][context].keys() if k not in exclusion_list])
        print("1) context in D with symbols: D[{}]['{}'] = {}, excluded = {}".format(n, context, D[n][context], exclusion_list))

        # if there are non-zero values in the context, use them to encode symbol or esc
        keys = D[n][context].keys()
        if sum_values > 0:
            p = 1 / sum_values
            print("2) non-zero context values found: sum_values = {}, singular p = {}".format(sum_values, p))

            if symbol in keys and D[n][context][symbol] != 0:
                prev_prob, next_prob = 0, 0
                for key in keys:
                    prev_prob = next_prob
                    next_prob += D[n][context][key] * p
                    if key == symbol:
                        break

                print("3) symbol found and non-zero, encode it: symbol = {}, low prob = {}, high prob = {}".format(symbol, prev_prob, next_prob))

                D[n][context][symbol] += 1
                out = {"symbol": symbol, "l_prob": prev_prob, "h_prob": next_prob}
            else:
                # if symbol not in keys (or symbol prob 0), encode esc symbol
                exclusion_list.extend([k for k in keys if not (k == "esc" or k in exclusion_list or D[n][context][k] == 0)])

                prev_prob = 0
                next_prob = D[n][context]["esc"] * p

                if symbol in keys:
                    # if symbol in keys, increment it and esc as count must be zero
                    print("4) symbol count is zero, escape: symbol = 'esc', low prob = {}, high prob = {}".format(prev_prob, next_prob))
                    D[n][context][symbol] += 1
                    D[n][context]["esc"] += 1
                else:
                    # if symbol not in keys, add it
                    print("5) symbol not in context, escape: symbol = 'esc', low prob = {}, high prob = {}".format(prev_prob, next_prob))
                    D[n][context][symbol] = 0

                out = {"symbol": "esc", "l_prob": prev_prob, "h_prob": next_prob}
        else:
            # if all values in context section are zero, encode esc with probability interval 0 - 1
            if symbol in keys:
                print("6) all symbols, incl symbol, zero, escape: symbol = 'esc', low prob = 0, high prob = 1")
                # if symbol in keys, increment it as count must be zero and increment sc to show there's a non-zero
                D[n][context][symbol] += 1
                D[n][context]["esc"] += 1
            else:
                print("7) all symbols zero, symbol never observed, escape: symbol = 'esc', low prob = 0, high prob = 1")
                # if symbol not in keys, add it
                D[n][context][symbol] = 0

            out = {"symbol": "esc", "l_prob": 0.0, "h_prob": 1.0}
    else:
        # if context not in D, add it and output esc
        print("8) context never observed, escape: symbol = 'esc', low prob = 0, high prob = 1")
        D[n][context] = {"esc": 0, symbol: 0}
        out = {"symbol": "esc", "l_prob": 0.0, "h_prob": 1.0}

    return out, exclusion_list


def order_minus1(symbol):

    char_code = ord(symbol)
    prev_p = char_code * (1 / 128)
    p = (char_code + 1) * (1 / 128)

    print("9) order -1 context: p interval = [{}, {}), code = {}".format(prev_p, p, char_code))

    out = {"symbol": symbol, "l_prob": prev_p, "h_prob": p}

    return out


def arithmetic_encoder(l_old, h_old, e3_count, m, ppm_output):
    symbol = ppm_output["symbol"]
    l_prob = ppm_output["l_prob"]
    h_prob = ppm_output["h_prob"]
    out = ''

    l_old = int(l_old, 2)
    h_old = int(h_old, 2)

    print("low prob = {}, high prob = {}".format(l_prob, h_prob))

    l_new = l_old + math.floor((h_old - l_old + 1) * l_prob)
    h_new = l_old + math.floor((h_old - l_old + 1) * h_prob) - 1

    print("int l_old -> l_new: {} -> {}".format(l_old, l_new))
    print("int h_old -> h_new: {} -> {}".format(h_old, h_new))

    l_new = format(l_new, 'b')
    l = l_new + '0' * (m - len(l_new))
    h_new = format(h_new, 'b')
    h = h_new + '1' * (m - len(h_new))

    print("binary versions: l = {}, h = {}".format(l, h))

    e1e2_condition = (l[0] == h[0])
    e3_condition = (l[0] != h[0] and l[1] == '1' and h[1] == '0')

    while (e1e2_condition or e3_condition) is True:
        if e1e2_condition:
            print("e1/e2 condition")

            e3_bit = '0' if l[0] == '1' else '1'
            out += l[0] + e3_bit * e3_count
            e3_count = 0

            l = l[1:] + '0'
            h = h[1:] + '1'

        elif e3_condition:
            print("e3 condition")

            l = '0' + l[2:] + '0'
            h = '1' + h[2:] + '1'
            e3_count += 1

        e1e2_condition = (l[0] == h[0])
        e3_condition = ((l[0] != h[0]) and l[1] == '1' and h[1] == '0')

    print("Final updated binary values: l = {}, h = {}, output = {}".format(l, h, out), end='\n\n')

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


sequence, file = get_file_input()
print("Sequence to encode:", sequence, end='\n\n')

N = 4
sequence = "-" * N + sequence
D = [{} for i in range(N + 1)]
outputs = []
codeword = ''
m = 9
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
            output, excluded = ppm_step(symb, n, context, excluded)
        else:  # n == -1
            output = order_minus1(symb)

        symbol_outputs.append((n, output))

        encoding = arithmetic_encoder(low, high, e3_counter, m, output)
        low = encoding["l"]
        high = encoding["h"]
        # print("Low = {}, High = {}".format(low, high))
        e3_counter = encoding["e3"]
        code += encoding["output"]

        if output["symbol"] == symb:
            if code != '':
                codeword += code
            outputs.append(symbol_outputs)
            break
        else:
            n -= 1

terminal_code = terminate_encoding(low, e3_counter)
codeword += terminal_code

output_file(codeword, file)

# print("D =")
# for i in range(N+1):
#     print(D[i])
#
# print("\n\nOUTPUTS =")
# for i in range(len(outputs)):
#     print(outputs[i])
#
# print("\n\nSEQUENCE =", sequence[N:])
print("ENCODING =", codeword)
