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
        exit(1)

    f = open(file_name, 'r', encoding="ascii")

    if f.mode != 'r':
        print("Error")
        exit(1)

    file_contents = f.read()

    return file_contents, name


def output_file(encoded_seq, file_name):

    f = open(file_name + ".lz", "w")
    encoded_seq = str(encoded_seq)
    f.write(encoded_seq)
    f.close()


def get_interval(symb):

    keys = list(table.keys())
    prev_p = table[keys[keys.index(symb) - 1]]
    p = table[symb]

    print("1) Interval found: symbol = {}, interval = [{},{}) = [{},{})".format(symb, table[keys[keys.index(symb) - 1]], table[symb], prev_p, p))

    if prev_p > p:
        print("Error, probability interval calculated incorrectly: [{}, {})".format(prev_p, p))
        exit(1)

    return prev_p, p


def arithmetic_encoder(l_old_bin, h_old_bin, e3_count, m, l_prob, h_prob, total):

    print("2) encoding inputs: low = {}, high = {}, e3 count = {}, low prob = {}, high_prob = {}".format(l_old_bin, h_old_bin, e3_count, l_prob, h_prob))

    out = ''
    l_old = int(l_old_bin, 2)
    h_old = int(h_old_bin, 2)

    print(" a. converting to binary: low = {}, high = {}".format(l_old_bin, h_old_bin))

    l_new_bin = l_old + math.floor(((h_old - l_old + 1) * l_prob) / total)
    h_new_bin = l_old + math.floor(((h_old - l_old + 1) * h_prob) / total) - 1

    l_new = format(l_new_bin, 'b')
    l = l_new + '0' * (m - len(l_new))
    h_new = format(h_new_bin, 'b')
    h = h_new + '1' * (m - len(h_new))

    print(" b. new low and high: low = {} -> {} -> {}, high = {} -> {} -> {}".format(l_new_bin, l_new, l, h_new_bin, h_new, h))
    print(" c. checking conditions...")

    while ((l[0] == h[0]) or (l[1] == '1' and h[1] == '0')) is True:

        if l[0] == h[0]:
            e3_bit = '0' if l[0] == '1' else '1'
            out += l[0] + e3_bit * e3_count
            e3_count = 0
            l = l[1:] + '0'
            h = h[1:] + '1'
            print("  i. e1/e2 condition: low = {}, high = {}".format(l, h))

        if l[1] == '1' and h[1] == '0':
            l = '0' + l[2:] + '0'
            h = '1' + h[2:] + '1'
            e3_count += 1
            print("  ii. e3 condition: low = {}, high = {}".format(l, h))

    print(" d. updates and outputs: low = {}, high = {}, output = {}, e3 count = {}".format(l, h, out, e3_count), end='\n\n')

    return l, h, e3_count, out


def terminate_encoding(l, e3):

    print("3) Terminating encoding: final low = {}, e3 count = {}".format(l, e3))

    if e3 > 0:
        msb = l[0]
        e3_bit = '0' if msb == '1' else '1'
        out = msb + e3_bit * e3 + l[1:]
        print(" a. complementing output: e3 bits = {}".format(e3_bit))
    else:
        out = l
        print(" b. no complements needed")

    print(" c. outputting: {}".format(out))
    return out


sequence, file = get_file_input()
print("Sequence to encode:", sequence)

# no_chars = 128
# table_vals = {chr(v): v+1 for v in range(128)}
# table = {'': 0}
# table.update(table_vals)

# max_char = 3
# table = {'': 0, 'a': 1, 'b': 2, 'c': 3}
max_char = 48
table = {'': 0, 'a': 16, 'b': 32, 'c': 48}

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
    print("ENCODING SYMBOL {} = '{}'".format(length, str(symbol)))

    low_prob, high_prob = get_interval(symbol)
    outputs.append({"symbol": symbol, "low": low_prob, "high": high_prob})

    low, high, e3_counter, codeword = arithmetic_encoder(low, high, e3_counter, m, low_prob, high_prob, max_char)
    code += codeword

terminal_code = terminate_encoding(low, e3_counter)
code += terminal_code

print("Output encoding:", code)

output_file(code, file)
