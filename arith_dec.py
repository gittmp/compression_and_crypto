import math
import pickle


class ArithmeticDecoder:
    def __init__(self):
        self.max_freq = 256
        self.freq_table = [n for n in range(self.max_freq + 1)]
        print("frequency array:", self.freq_table)
        self.m = 8
        self.e3 = 0
        self.low = 0
        self.high = 255

    def decode(self, sequence):
        output = bytearray()
        start = 0

        while True:
            tag_bin = sequence[start:start + self.m]

            if tag_bin == '':
                break

            tag = int(tag_bin, 2)

            frequency = (((tag - self.low + 1) * self.max_freq) - 1) / (self.high - self.low + 1)

            # print("freq = {}, tag = {} = {}".format(frequency, tag_bin, tag))

            for f in range(self.max_freq):
                if self.freq_table[f] > frequency:
                    # print("table[{}] = {} > {}".format(f, self.freq_table[f], frequency))

                    output.append(f - 1)

                    low_prev = self.low
                    high_prev = self.high

                    self.low = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[f - 1]) / self.max_freq)
                    self.high = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[f]) / self.max_freq) - 1

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

                        sequence = sequence[:start] + str(1 - int(sequence[start + 1])) + sequence[start + 2:]

                    break

        output = bytes(output)

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


with open('encoding.lz', 'rb') as file:
    encoding = pickle.load(file)

print("Input sequence:", encoding)

decoder = ArithmeticDecoder()
message, info = decoder.full_decoding(encoding)

print("Input file size:", info[0])
print("Output file size:", info[1])
print("Output sequence:", message)
