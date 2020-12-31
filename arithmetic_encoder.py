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


def get_interval(symb, total):

    keys = list(table.keys())
    prev_p = table[keys[keys.index(symb) - 1]] / total
    p = table[symb] / total

    if prev_p > p:
        print("Error, probability interval calculated incorrectly: [{}, {})".format(prev_p, p))
        exit(1)

    # if symb == ' ':
    #     print("ENCODING A SPACE: chosen interval = [{}, {}), ord(space) = {}".format(prev_p, p, ord(' ')))
    #     exit(2)

    return prev_p, p


def arithmetic_encoder(l_old_bin, h_old_bin, e3_count, m, l_prob, h_prob):

    out = ''
    l_old = int(l_old_bin, 2)
    h_old = int(h_old_bin, 2)

    print(" a. inputs: low = {} -> {}, high = {} -> {}, e3 count = {}, low prob = {}, high_prob = {}".format(l_old_bin, l_old, h_old_bin, h_old, e3_count, l_prob, h_prob))

    l_new_bin = l_old + math.floor((h_old - l_old + 1) * l_prob)
    h_new_bin = l_old + math.floor((h_old - l_old + 1) * h_prob) - 1

    l_new = format(l_new_bin, 'b')
    l = l_new + '0' * (m - len(l_new))
    h_new = format(h_new_bin, 'b')
    h = h_new + '1' * (m - len(h_new))

    print(" b. new low and high: low = {} -> {} -> {}, high = {} -> {} -> {}".format(l_new_bin, l_new, l, h_new_bin, h_new, h))

    while ((l[0] == h[0]) or (l[1] == '1' and h[1] == '0')) is True:

        if l[0] == h[0]:
            e3_bit = '0' if l[0] == '1' else '1'
            out += l[0] + e3_bit * e3_count
            e3_count = 0
            l = l[1:] + '0'
            h = h[1:] + '1'
            print(" e1/e2 condition: low = {}, high = {}".format(l, h))

        if l[1] == '1' and h[1] == '0':
            l = '0' + l[2:] + '0'
            h = '1' + h[2:] + '1'
            e3_count += 1
            print(" e3 condition: low = {}, high = {}".format(l, h))

    print(" c. updates and outputs: low = {}, high = {}, output = {}, e3 count = {}".format(l, h, out, e3_count), end='\n\n')

    return l, h, e3_count, out


def terminate_encoding(l, e3):

    if e3 > 0:
        msb = l[0]
        e3_bit = '0' if msb == '1' else '1'
        out = msb + e3_bit * e3 + l[1:]
    else:
        out = l

    return out


sequence, file = get_file_input()
print("Sequence to encode:", sequence)

no_chars = 128
table_vals = {chr(v): v+1 for v in range(128)}
table = {'': 0}
table.update(table_vals)
print("char table:", table, end='\n\n')

outputs = []
code = ''
m = 8
low = '0' * m
high = '1' * m
e3_counter = 0
length = 0

for symbol in sequence:
    length += 1
    print("ENCODING SYMBOL {} = {}".format(length, symbol))

    low_prob, high_prob = get_interval(symbol, no_chars)
    outputs.append({"symbol": symbol, "low": low_prob, "high": high_prob})

    low, high, e3_counter, codeword = arithmetic_encoder(low, high, e3_counter, m, low_prob, high_prob)
    code += codeword

terminal_code = terminate_encoding(low, e3_counter)
code += terminal_code

print("Output encoding:", code)

output_file(code, file)