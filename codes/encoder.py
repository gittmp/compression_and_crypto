import sys
import os
import math
import pickle


class PPMEncoder:

    def __init__(self, max_freq=256):
        self.max_freq = max_freq
        self.m = 8
        self.e3 = 0

        self.low = 0
        self.high = 0
        for h in range(self.m):
            self.high += 2 ** h

        self.N = 6
        self.D = [{} for _ in range(self.N + 1)]
        self.freq_table = self.make_freq_table()
        self.output = []

        self.counts = [0] * 11

    def count(self, i):
        if 0 <= i <= 31:
            self.counts[0] += 1
        elif 32 <= i <= 47:
            self.counts[1] += 1
        elif 48 <= i <= 57:
            self.counts[2] += 1
        elif 58 <= i <= 64:
            self.counts[3] += 1
        elif 65 <= i <= 90:
            self.counts[4] += 1
        elif 91 <= i <= 96:
            self.counts[5] += 1
        elif 97 <= i <= 122:
            self.counts[6] += 1
        elif 123 <= i <= 126:
            self.counts[7] += 1
        elif 127 <= i <= 160:
            self.counts[8] += 1
        elif 161 <= i <= 191:
            self.counts[9] += 1
        elif 192 <= i <= 255:
            self.counts[10] += 1

    def make_freq_table(self, s=0.67):
        distribution = [1] * self.max_freq

        for i in range(len(distribution)):
            if 0 <= i <= 31:
                # 0-31 is level 3
                distribution[i] = math.floor(math.exp(s * 3))
            elif 32 <= i <= 47:
                # 32 - 47 is level 4
                distribution[i] = math.floor(math.exp(s * 4))
            elif 48 <= i <= 57:
                # 48 - 57 is level 3
                distribution[i] = math.floor(math.exp(s * 3))
            elif 58 <= i <= 64:
                # 58 - 64 is level 2
                distribution[i] = math.floor(math.exp(s * 2))
            elif 65 <= i <= 90:
                # 65 - 90 is level 3
                distribution[i] = math.floor(math.exp(s * 3))
            elif 91 <= i <= 96:
                # 91 - 96 is level 3
                distribution[i] = math.floor(math.exp(s * 3))
            elif 97 <= i <= 122:
                # 97 - 122 is level 5
                distribution[i] = math.floor(math.exp(s * 5))
            elif 123 <= i <= 126:
                # 123 - 126 is level 3
                distribution[i] = math.floor(math.exp(s * 3))
            elif 127 <= i <= 160:
                # 127 - 160 is level 1
                distribution[i] = math.floor(math.exp(s * 1))
            elif 161 <= i <= 191:
                # 161 - 191 is level 1
                distribution[i] = math.floor(math.exp(s * 1))
            elif 192 <= i <= 255:
                # 192 - 255 is level 1
                distribution[i] = math.floor(math.exp(s * 1))

        cum_distribution = [0]
        for j in range(len(distribution)):
            value = cum_distribution[j] + distribution[j]
            cum_distribution.append(value)

        self.max_freq = cum_distribution[-1]

        print("Cumulative frequency table:")
        print("   length =", len(cum_distribution))
        print("   max freq =", self.max_freq)
        # print("   values =", cum_distribution)

        return cum_distribution

    def encode(self, sequence):
        byte_count = 0
        b = -1

        while b < len(sequence) - 1:
            b += 1
            byte_count += 1
            byte = sequence[b]

            # self.count(byte)

            order = self.N
            excluded = []
            # print("\nBYTE NO. = {}, BYTE = {}".format(byte_count, byte))

            while order > -2:
                # print("ORDER =", order)
                if order > -1:

                    if b < order:
                        # byts = ["-"] * (order - b)
                        char_list = [116, 104, 101, 32, 116, 104]
                        byts = char_list[:order - b]

                        byts.extend([byt for byt in sequence[:b]])
                        context = str(byts)
                        # print("made context = ", context)
                    else:
                        context = str([byt for byt in sequence[b - order:b]])
                        # print("existing context = ", context)

                    probabilities, excluded = self.ppm_step(str(byte), order, context, excluded)
                    low_prob = probabilities['l_prob']
                    high_prob = probabilities['h_prob']
                    total = probabilities['sum']

                    result = self.encode_step(byte, order, low_prob, high_prob, total)

                    if not result:
                        self.m += 1
                        self.reset()
                        self.counts = [0] * 11
                        # print("increasing value of self.m to {}".format(self.m))
                        byte_count = 0
                        b = -1
                        break

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
            # print("restarting program")
            return False

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

        return True

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

    def reset(self):
        self.output = []
        self.e3 = 0
        self.low = 0

        self.high = 0
        for h in range(self.m):
            self.high += 2 ** h

        self.D = [{} for _ in range(self.N + 1)]

    def full_encoding(self, sequence):
        partial_encoding, no_bytes = self.encode(sequence)
        complete_encoding = self.terminate_encoding(partial_encoding)
        data = self.output_data(complete_encoding, no_bytes)
        data = (data[0], data[1], no_bytes)
        self.reset()

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

# print("\ncompressing sequence:", message)
# print("input file size:", info[2])
# print("output file size:", info[1])
# print("compression ratio:", info[0])

# print("\nencoding:", encoding)

print("\nFinal value of self.m = {}\n".format(encoder.m))
# print("\nCOUNTS = {}\n".format(encoder.counts))

# print("Encoding:", encoding[:25])
# print("Type:", type(encoding))

with open(file_name + '.lz', 'wb') as file:
    encoding = format(14, 'b').zfill(8) + encoding
    pickle.dump(encoding, file)

print("\nENCODING COMPLETE!!\n")
