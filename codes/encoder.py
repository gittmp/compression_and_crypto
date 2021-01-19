import sys
import os
import math


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

    @staticmethod
    def classify_byte(byte):
        if 0 <= byte <= 31:
            # 0-31 is level 3
            return 3
        elif 32 <= byte <= 47:
            # 32 - 47 is level 4
            return 4
        elif 48 <= byte <= 57:
            # 48 - 57 is level 3
            return 3
        elif 58 <= byte <= 64:
            # 58 - 64 is level 2
            return 2
        elif 65 <= byte <= 90:
            # 65 - 90 is level 3
            return 3
        elif 91 <= byte <= 96:
            # 91 - 96 is level 3
            return 3
        elif 97 <= byte <= 122:
            # 97 - 122 is level 5
            return 5
        elif 123 <= byte <= 126:
            # 123 - 126 is level 3
            return 3
        elif 127 <= byte <= 160:
            # 127 - 160 is level 1
            return 1
        elif 161 <= byte <= 191:
            # 161 - 191 is level 1
            return 1
        elif 192 <= byte <= 255:
            # 192 - 255 is level 1
            return 1

    def make_freq_table(self, s=0.55):
        distribution = [1] * self.max_freq

        for b in range(len(distribution)):
            x = self.classify_byte(b)
            distribution[b] = math.floor(math.exp(s * x))

        cum_distribution = [0]
        for j in range(len(distribution)):
            value = cum_distribution[j] + distribution[j]
            cum_distribution.append(value)

        self.max_freq = cum_distribution[-1]

        return cum_distribution

    def encode(self, sequence):
        byte_count = 0
        b = -1

        while b < len(sequence) - 1:
            b += 1
            byte_count += 1
            byte = sequence[b]
            order = self.N
            excluded = []
            # print("\nBYTE NO. = {}, BYTE = {}".format(byte_count, byte))

            while order > -2:
                if order > -1:

                    if b < order:
                        char_list = [116, 104, 101, 32, 116, 104]
                        byts = char_list[:order - b]

                        byts.extend([byt for byt in sequence[:b]])
                        context = str(byts)
                    else:
                        context = str([byt for byt in sequence[b - order:b]])

                    probabilities, excluded = self.ppm_step(str(byte), order, context, excluded)
                    low_prob = probabilities['l_prob']
                    high_prob = probabilities['h_prob']
                    total = probabilities['sum']

                    result = self.encode_step(byte, order, low_prob, high_prob, total)

                    if not result:
                        self.m += 1
                        self.reset()
                        byte_count = 0
                        b = -1
                        break

                    if probabilities['symbol'] == byte:
                        break
                    else:
                        order -= 1
                else:
                    self.encode_step(byte)
                    break

        return self.output, byte_count

    def encode_step(self, byte, n=-1, l_freq=None, h_freq=None, total=None):
        low_prev = self.low
        high_prev = self.high

        if n == -1:
            self.low = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[byte]) / self.max_freq)
            self.high = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[byte + 1]) / self.max_freq) - 1
        else:
            self.low = low_prev + math.floor(((high_prev - low_prev + 1) * l_freq) / total)
            self.high = low_prev + math.floor(((high_prev - low_prev + 1) * h_freq) / total) - 1

        if self.low >= self.high:
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

    def increment(self, symbol):
        return 1

    def ppm_step(self, symbol, n, c, exclusion_list):
        if c in self.D[n].keys():
            sum_values = sum([self.D[n][c][k] for k in self.D[n][c].keys() if k not in exclusion_list])

            # if there are non-zero values in the context, use them to encode symbol or esc
            keys = [k for k in self.D[n][c].keys() if k not in exclusion_list]
            if sum_values > 0:

                if symbol in keys and self.D[n][c][symbol] != 0:

                    prev_cum_freq, cum_freq = 0, 0
                    for key in keys:
                        prev_cum_freq = cum_freq
                        cum_freq += self.D[n][c][key]
                        if key == symbol:
                            break

                    increment = self.increment(symbol)
                    self.D[n][c][symbol] += increment
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
                        increment = self.increment(symbol)
                        self.D[n][c][symbol] += increment
                        self.D[n][c]["esc"] += 1
                    else:
                        # if symbol not in keys, add it
                        esc_count = self.D[n][c].pop("esc", 0)
                        self.D[n][c][symbol] = 0
                        self.D[n][c]["esc"] = esc_count

                    out = {"symbol": "esc", "l_prob": prev_cum_freq, "h_prob": cum_freq, "sum": sum_values}
            else:
                # if all values in context section are zero, encode esc with probability interval 0 - 1
                if symbol in keys:
                    # if symbol in keys, increment it as count must be zero and increment sc to show there's a non-zero
                    increment = self.increment(symbol)
                    self.D[n][c][symbol] += increment
                    self.D[n][c]["esc"] += 1
                else:
                    # if symbol not in keys, add it
                    esc_count = self.D[n][c].pop("esc", 0)
                    self.D[n][c][symbol] = 0
                    self.D[n][c]["esc"] = esc_count

                out = {"symbol": "esc", "l_prob": 0.0, "h_prob": 1.0, "sum": 1}
        else:
            # if context not in D, add it and output esc
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
print("File:", file)

# change to .tex in final implementation
if extension != ".tex":
    print("Extension:", extension)
    print("Not a LaTeX file!")
    exit(1)

with open(file, 'rb') as f:
    message = f.read()
    message += b'\x04'

encoder = PPMEncoder()
encoding, info = encoder.full_encoding(message)

# print("Input file size:", info[2])
# print("Output file size:", info[1])
# print("Compression ratio:", info[0])

with open(file_name + '.lz', 'w') as file:
    m_val = format(encoder.m, 'b').zfill(8)
    encoding = m_val + encoding
    file.write(encoding)

print("\nENCODING COMPLETE!!\n")
