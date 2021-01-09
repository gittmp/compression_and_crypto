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

    def decode(self, full_tag):
        output = bytearray()
        start = 0
        tag_bin = full_tag[start:start + self.m]

        while tag_bin != '':
            tag = int(tag_bin, 2)

            frequency = (((tag - self.low + 1) * self.max_freq) - 1) / (self.high - self.low + 1)
            bound = 0

            while self.freq_table[bound] <= frequency and bound < self.max_freq:
                bound += 1

            if bound >= self.max_freq:
                print("Decoding frequency bound not found")
                exit(1)

            output.append(bound - 1)

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

                start += 1

            while l[1] == '1' and h[1] == '0':
                l = l[0] + l[2:] + '0'
                h = h[0] + h[2:] + '1'

                self.low = int(l, 2)
                self.high = int(h, 2)

                full_tag = full_tag[:start] + str(1 - int(full_tag[start + 1])) + full_tag[start + 2:]

            tag_bin = full_tag[start:start + self.m]

        output = bytes(output)[:-1]

        return output

    def output_data(self, seq, output):
        enc_size = len(seq) / self.m
        dec_size = len(output)
        ratio = dec_size / enc_size

        return enc_size, dec_size, ratio

    def full_decoding(self, sequence):
        decoding = self.decode(sequence)
        data = self.output_data(sequence, decoding)

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
