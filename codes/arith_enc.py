import sys
import os
import math
import pickle


class ArithmeticEncoder:

    def __init__(self):
        self.max_freq = 256
        self.freq_table = [n for n in range(self.max_freq + 1)]
        # print("frequency array:", self.freq_table)
        self.m = 8
        self.e3 = 0
        self.low = 0
        self.high = 255

    def encode(self, sequence):
        byte_count = 0
        output = []

        for byte in sequence:
            byte_count += 1

            low_prev = self.low
            high_prev = self.high

            self.low = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[byte]) / self.max_freq)
            self.high = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[byte + 1]) / self.max_freq) - 1

            l = format(self.low).zfill(self.m)
            h = format(self.high).zfill(self.m)

            while (l[0] == h[0]) or (l[1] == '1' and h[1] == '0'):
                l = format(self.low, 'b').zfill(self.m)
                h = format(self.high, 'b').zfill(self.m)

                if l[0] == h[0]:
                    # e1/e2 condition
                    output.append(l[0])
                    e3_bit = '0' if l[0] == '1' else '1'

                    l = l[1:] + '0'
                    h = h[1:] + '1'
                    self.low = int(l, 2)
                    self.high = int(h, 2)

                    output.extend([e3_bit] * self.e3)
                    self.e3 = 0

                elif l[1] == '1' and h[1] == '0':
                    l = l[0] + l[2:] + '0'
                    h = h[0] + h[2:] + '1'
                    self.low = int(l, 2)
                    self.high = int(h, 2)

                    self.e3 += 1

        return output, byte_count

    def terminate_encoding(self, output):
        l = format(self.low, 'b').zfill(self.m)

        output.append(l[0])
        output.extend(['1'] * self.e3)
        output.append(l[1:])
        outbits = "".join(output)

        self.e3 = 0
        self.low = 0
        self.high = 255

        return outbits

    def output_data(self, outbits, byte_count):
        output_size = len(outbits) / self.m
        ratio = byte_count / output_size

        return ratio, output_size

    def full_encoding(self, sequence):
        partial_encoding, no_bytes = self.encode(sequence)
        finished_encoding = self.terminate_encoding(partial_encoding)
        data = self.output_data(finished_encoding, no_bytes)
        data = (data[0], data[1], no_bytes)

        return finished_encoding, data


file = sys.argv[1]
file_name, extension = os.path.splitext(file)
# print("File name: ", file_name)

# change to .tex in final implementation
if extension != ".tex":
    print("Not a LaTeX file!")
    exit(1)

with open(file, 'rb') as f:
    message = f.read()

encoder = ArithmeticEncoder()
encoding, info = encoder.full_encoding(message)

# print("compressing sequence:", message)
# print("input file size:", info[2])
# print("output file size:", info[1])
# print("compression ratio:", info[0])
#
# print("\nencoding:", encoding)

with open(file_name + '.lz', 'wb') as file:
    pickle.dump(encoding, file)
