import sys
import os
import math
import pickle


class ArithmeticDecoder:
    def __init__(self, freq_table=None, max_freq=256):
        self.max_freq = max_freq
        self.m = 8
        self.e3 = 0
        self.low = 0
        self.high = 255

        if freq_table is None:
            self.freq_table = [n for n in range(self.max_freq + 1)]
        else:
            self.freq_table = freq_table

        self.N = 4
        self.D = [{} for _ in range(self.N + 1)]
        self.start = 0
        self.full_tag = ''
        self.binary_tag = ''
        self.output = []

    def decode(self, full_tag):
        self.full_tag = full_tag
        self.binary_tag = self.full_tag[:self.m]
        byte_count = 0

        while self.binary_tag != '':
            byte_count += 1
            order = self.N
            excluded = []

            # while order > -2:
            #     if order > -1:
            #         if len(self.output) < order:
            #             context = str((["-"] * (order - len(self.output))).extend(self.output))
            #         else:
            #             context = str(self.output[byte_count - order:])

            self.decode_step()

            # print("self.output = {}".format(self.output))

        self.output = bytes(self.output)[:-1]
        # print("self.output = {}".format(self.output))

        return self.output

    def decode_step(self, n=-1, c=None, exclusion_list=None):
        tag = int(self.binary_tag, 2)

        frequency = (((tag - self.low + 1) * self.max_freq) - 1) / (self.high - self.low + 1)

        bound = 0
        while self.freq_table[bound] <= frequency and bound < self.max_freq:
            bound += 1

        if bound >= self.max_freq:
            print("Decoding frequency bound not found")
            exit(1)

        self.output.append(bound - 1)

        low_prev = self.low
        high_prev = self.high

        self.low = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[bound - 1]) / self.max_freq)
        self.high = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[bound]) / self.max_freq) - 1

        l = format(self.low, 'b').zfill(self.m)
        h = format(self.high, 'b').zfill(self.m)

        while l[0] == h[0]:
            l = l[1:] + '0'
            h = h[1:] + '1'

            self.low = int(l, 2)
            self.high = int(h, 2)

            self.start += 1

        while l[1] == '1' and h[1] == '0':
            l = l[0] + l[2:] + '0'
            h = h[0] + h[2:] + '1'

            self.low = int(l, 2)
            self.high = int(h, 2)

            self.full_tag = self.full_tag[:self.start] + str(1 - int(self.full_tag[self.start + 1])) + self.full_tag[self.start + 2:]

        self.binary_tag = self.full_tag[self.start:self.start + self.m]

    def backtrack_update(self, i, decoded_sequence, n, symb):
        while n <= self.N:
            # find nth order context
            c = decoded_sequence[i - n:]
            # print("Updating D with: n = {}, i = {}, context = {}, symbol = {}".format(n, i, c, symb))

            # update count of context-symbol in D
            if c in self.D[n].keys():
                if symb in self.D[n][c].keys():
                    if self.D[n][c][symb] == 0:
                        # if the symbol exists but is zero increment esc count (method B) as well as symbol count
                        self.D[n][c]["esc"] += 1
                    self.D[n][c][symb] += 1
                else:
                    esc_count = self.D[n][c].pop("esc", 0)
                    self.D[n][c][symb] = 0
                    self.D[n][c]["esc"] = esc_count
            else:
                self.D[n][c] = {symb: 0, "esc": 0}

            # increment n
            n += 1

    def output_data(self, seq, output):
        enc_size = len(seq) / self.m
        dec_size = len(output)
        ratio = dec_size / enc_size

        return enc_size, dec_size, ratio

    def full_decoding(self, sequence):
        decoding = self.decode(sequence)
        data = self.output_data(sequence, decoding)

        self.e3 = 0
        self.low = 0
        self.high = 255
        self.start = 0
        self.full_tag = ''
        self.binary_tag = ''
        self.output = []

        return decoding, data


file = sys.argv[1]
file_name, extension = os.path.splitext(file)
print("File name: ", file_name)

if extension != ".lz":
    print("Not a compatible compressed file!")
    exit(1)

with open(file, 'rb') as f:
    encoding = pickle.load(f)

decoder = ArithmeticDecoder()
message, info = decoder.full_decoding(encoding)

print("Input sequence:", encoding)
print("Input file size:", info[0])
print("Output file size:", info[1])
print("Output sequence:", message)

with open(file_name + "-decoded.tex", 'wb') as f:
    f.write(message)
