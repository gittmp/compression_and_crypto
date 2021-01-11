import sys
import os
import math
import pickle


class PPMEncoder:

    def __init__(self, freq_table=None, max_freq=256):
        self.max_freq = max_freq
        self.m = 13
        self.e3 = 0
        self.low = 0
        self.high = 0
        for h in range(self.m):
            self.high += 2 ** h

        self.N = 4
        self.D = [{} for _ in range(self.N + 1)]

        if freq_table is None:
            self.freq_table = [n for n in range(self.max_freq + 1)]
        else:
            self.freq_table = freq_table

        self.output = []

    def printD(self):
        print("Data table D:")
        for p in range(len(self.D)):
            print(self.D[p])

    def encode(self, sequence):
        byte_count = 0

        for b in range(0, len(sequence)):
            byte_count += 1
            byte = sequence[b]

            order = self.N
            excluded = []
            # print("\nBYTE NO. = {}, BYTE = {}".format(byte_count, byte))

            while order > -2:
                # print("ORDER =", order)
                if order > -1:

                    if b < order:
                        byts = ["-"] * (order - b)
                        byts.extend([byt for byt in sequence[:b]])
                        context = str(byts)
                        # print("made context = ", context)
                    else:
                        context = str([byt for byt in sequence[b - order:b]])
                        # print("existing context = ", context)

                    # try:
                    #     # print("found context: D[{}][{}] = {}".format(order, context, self.D[order][context]))
                    # except KeyError:
                    #     # print("context not found in D[{}]".format(order))

                    probabilities, excluded = self.ppm_step(str(byte), order, context, excluded)
                    low_prob = probabilities['l_prob']
                    high_prob = probabilities['h_prob']
                    total = probabilities['sum']

                    self.encode_step(byte, order, low_prob, high_prob, total)

                    if probabilities['symbol'] == byte:
                        # print("breaking!")
                        break
                    else:
                        order -= 1
                else:
                    # print("encoding in order -1, byte =", byte)
                    self.encode_step(byte)
                    break

        return self.output, byte_count

    def encode_step(self, byte, n=-1, l_freq=None, h_freq=None, total=None):
        low_prev = self.low
        high_prev = self.high

        if n == -1:
            self.low = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[byte]) / self.max_freq)
            self.high = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[byte + 1]) / self.max_freq) - 1
            # print("Bounds = [{},{}), new low = {}, new high = {}".format(self.freq_table[byte], self.freq_table[byte + 1], self.low, self.high))
        else:
            self.low = low_prev + math.floor(((high_prev - low_prev + 1) * l_freq) / total)
            self.high = low_prev + math.floor(((high_prev - low_prev + 1) * h_freq) / total) - 1
            # print("Bounds = [{},{}), new low = {}, new high = {}".format(l_freq, h_freq, self.low, self.high))

        if self.low >= self.high:
            # print("\noh no low and high are equal (or incorrect order) eeeeek")
            # print("self.low = {}, self.high = {}".format(self.low, self.high))
            exit(1)

        l = format(self.low).zfill(self.m)
        h = format(self.high).zfill(self.m)

        while (l[0] == h[0]) or (l[1] == '1' and h[1] == '0'):
            l = format(self.low, 'b').zfill(self.m)
            h = format(self.high, 'b').zfill(self.m)

            if l[0] == h[0]:
                # e1/e2 condition
                self.output.append(l[0])
                e3_bit = '0' if l[0] == '1' else '1'

                l = l[1:] + '0'
                h = h[1:] + '1'
                self.low = int(l, 2)
                self.high = int(h, 2)

                self.output.extend([e3_bit] * self.e3)
                self.e3 = 0

            elif l[1] == '1' and h[1] == '0':
                l = l[0] + l[2:] + '0'
                h = h[0] + h[2:] + '1'
                self.low = int(l, 2)
                self.high = int(h, 2)

                self.e3 += 1

        # print("   updated to: low = {}, high = {}".format(self.low, self.high))

    def terminate_encoding(self, output):
        l = format(self.low, 'b').zfill(self.m)

        output.append(l[0])
        output.extend(['1'] * self.e3)
        output.append(l[1:])
        outbits = "".join(output)

        return outbits

    def ppm_step(self, symbol, n, c, exclusion_list):
        if c in self.D[n].keys():
            sum_values = sum([self.D[n][c][k] for k in self.D[n][c].keys() if k not in exclusion_list])
            # print("1) context in D with symbols: D[{}]['{}'] = {}, excluded = {}".format(n, context, self.[n][context], exclusion_list))

            # if there are non-zero values in the context, use them to encode symbol or esc
            keys = [k for k in self.D[n][c].keys() if k not in exclusion_list]
            if sum_values > 0:
                # print("2) non-zero context values found: sum_values = {}, excluded = {}".format(sum_values, exclusion_list))
                # print("   table = {}".format(self.D[n][c]))

                if symbol in keys and self.D[n][c][symbol] != 0:

                    prev_cum_freq, cum_freq = 0, 0
                    for key in keys:
                        prev_cum_freq = cum_freq
                        cum_freq += self.D[n][c][key]
                        if key == symbol:
                            break

                    # print("3) symbol found and non-zero, encode it: symbol = {}, low prob = {}/{}, high prob = {}/{}".format(symbol, prev_cum_freq, sum_values, cum_freq, sum_values))

                    self.D[n][c][symbol] += 1
                    out = {"symbol": int(symbol), "l_prob": prev_cum_freq, "h_prob": cum_freq, "sum": sum_values}
                else:
                    # if symbol not in keys (or symbol prob 0), encode esc symbol
                    exclusion_list.extend([k for k in keys if not (k == "esc" or k in exclusion_list or self.D[n][c][k] == 0)])

                    prev_cum_freq, cum_freq = 0, 0
                    for key in keys:
                        prev_cum_freq = cum_freq
                        cum_freq += self.D[n][c][key]
                        if key == "esc":
                            break

                    if symbol in keys:
                        # if symbol in keys, increment it and esc (as count must be zero)
                        # print("4) symbol count is zero, escape: symbol = 'esc', low prob = {}, high prob = {}".format(prev_cum_freq, cum_freq))
                        self.D[n][c][symbol] += 1
                        self.D[n][c]["esc"] += 1
                    else:
                        # if symbol not in keys, add it
                        # print("5) symbol not in context, escape: symbol = 'esc', low prob = {}, high prob = {}".format(prev_cum_freq, cum_freq))
                        esc_count = self.D[n][c].pop("esc", 0)
                        self.D[n][c][symbol] = 0
                        self.D[n][c]["esc"] = esc_count

                    out = {"symbol": "esc", "l_prob": prev_cum_freq, "h_prob": cum_freq, "sum": sum_values}
            else:
                # if all values in context section are zero, encode esc with probability interval 0 - 1
                if symbol in keys:
                    # print("6) all symbols, incl symbol, zero, escape: symbol = 'esc', low prob = 0, high prob = 1")
                    # if symbol in keys, increment it as count must be zero and increment sc to show there's a non-zero
                    self.D[n][c][symbol] += 1
                    self.D[n][c]["esc"] += 1
                else:
                    # print("7) all symbols zero, symbol never observed, escape: symbol = 'esc', low prob = 0, high prob = 1")
                    # if symbol not in keys, add it
                    esc_count = self.D[n][c].pop("esc", 0)
                    self.D[n][c][symbol] = 0
                    self.D[n][c]["esc"] = esc_count

                out = {"symbol": "esc", "l_prob": 0.0, "h_prob": 1.0, "sum": 1}
        else:
            # if context not in D, add it and output esc
            # print("8) context never observed, escape: symbol = 'esc', low prob = 0, high prob = 1")
            self.D[n][c] = {symbol: 0, "esc": 0}
            out = {"symbol": "esc", "l_prob": 0.0, "h_prob": 1.0, "sum": 1}

        return out, exclusion_list

    def output_data(self, outbits, byte_count):
        output_size = len(outbits) / self.m
        ratio = byte_count / output_size

        return ratio, output_size

    def full_encoding(self, sequence):
        partial_encoding, no_bytes = self.encode(sequence)
        complete_encoding = self.terminate_encoding(partial_encoding)
        data = self.output_data(complete_encoding, no_bytes)
        data = (data[0], data[1], no_bytes)

        self.output = []
        self.e3 = 0
        self.low = 0

        self.high = 0
        for h in range(self.m):
            self.high += 2 ** h

        return complete_encoding, data


file = sys.argv[1]
file_name, extension = os.path.splitext(file)
print("File name: ", file_name)

# change to .tex in final implementation
if extension != ".tex":
    print("Not a LaTeX file!")
    exit(1)

with open(file, 'rb') as f:
    message = f.read()
    message += b'\x04'

encoder = PPMEncoder()
encoding, info = encoder.full_encoding(message)

# print()
# encoder.printD()

# print("\ncompressing sequence:", message)
# print("input file size:", info[2])
# print("output file size:", info[1])
# print("compression ratio:", info[0])

# print("\nencoding:", encoding)

with open(file_name + '.lz', 'wb') as file:
    pickle.dump(encoding, file)
