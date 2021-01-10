import sys
import os
import math
import pickle


class PPMDecoder:
    def __init__(self, freq_table=None, max_freq=256):
        self.max_freq = max_freq
        self.m = 10
        self.e3 = 0
        self.low = 0
        self.high = 1024

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

    def printD(self):
        print("Data table D:")
        for p in range(len(self.D)):
            print(self.D[p])

    def decode(self, full_tag):
        self.full_tag = full_tag
        self.binary_tag = self.full_tag[:self.m]
        byte_count = 0

        while self.binary_tag != '' and byte_count < 100:
            byte_count += 1
            order = self.N
            excluded = []
            print("\nBYTE NO. =", byte_count)

            while order > -2:
                print("ORDER =", order)
                if order > -1:
                    # find corresponding context to current order
                    if len(self.output) < order:
                        byts = ["-"] * (order - len(self.output))
                        byts.extend(self.output)
                        context = str(byts)
                        print("made context =", context)
                    else:
                        context = str(self.output[byte_count - order - 1:])
                        print("existing context =", context)

                    # search current order for that context
                    # if not found:
                    if context not in self.D[order].keys():
                        # no need to update self.low and self.high on this esc as low_prob = 0.0 and high_prob = 1.0
                        # decrement order and repeat
                        print("context not in D[{}]".format(order))
                        order -= 1
                    # if found:
                    else:
                        # check if corresponding table row contains any non-zero entries
                        sum_values = sum([self.D[order][context][k] for k in self.D[order][context].keys() if k not in excluded])

                        # if no no-zero entries:
                        if sum_values == 0:
                            # no need to update self.low and self.high on this esc as low_prob = 0.0 and high_prob = 1.0
                            # decrement order and repeat
                            print("no non-zero entries in D[{}]".format(order))
                            order -= 1
                        # if there are non-zero entries:
                        else:
                            print("non-zero entries found in D[{}]".format(order))

                            found, excluded, symbol = self.ppm_update(sum_values, order, context, excluded)
                            self.process_lht()

                            # if PPM found the correct byte:
                            if found:
                                print("Found byte = {}".format(symbol))
                                # backtrack update PPM table orders n -> self.N given seen contexts/symbol
                                self.backtrack_update(byte_count, order, str(symbol))
                                break
                            # otherwise, if symbol is esc:
                            else:
                                # decrement order and repeat
                                print("Byte not found, symbol = 'esc'")
                                order -= 1
                # if order == -1:
                else:
                    # do normal AC to get symbol/updates
                    symbol = self.order_minus1_update()
                    self.process_lht()

                    print("decoding in order -1, found byte =", symbol)

                    # backtrack update PPM table orders 0 -> self.N given seen contexts/symbol
                    self.backtrack_update(byte_count, order, str(symbol))

                    break

            # print("self.output = {}".format(self.output))

        self.output = bytes(self.output)

        return self.output

    def ppm_update(self, sum_values, n, c, exclusion_list):
        tag = int(self.binary_tag, 2)

        # calculate frequency value (based on sum of non-zero entries)
        frequency = (((tag - self.low + 1) * sum_values) - 1) / (self.high - self.low + 1)
        print("frequency = ((({} - {} + 1) * {}) - 1) / ({} - {} + 1) = {}".format(tag, self.low, sum_values, self.high, self.low, frequency))

        # find low prob and high prob using PPM table, and associated symbol
        keys = list(self.D[n][c].keys())
        j = 0
        low_bound = 0
        high_bound = self.D[n][c][keys[0]]

        print("searching table: D[{}][{}] = {}".format(n, c, self.D[n][c]))

        while frequency >= high_bound:
            j += 1
            low_bound = high_bound
            high_bound += self.D[n][c][keys[j]]

        print("found bound = [{}, {}), j= {}".format(low_bound, high_bound, j))

        symbol = keys[j]

        # update self.low and self.high
        low_prev = self.low
        high_prev = self.high

        self.low = low_prev + math.floor((high_prev - low_prev + 1) * low_bound / sum_values)
        self.high = low_prev + math.floor((high_prev - low_prev + 1) * high_bound / sum_values) - 1

        # if symbol is esc:
        if symbol == "esc":
            # update the excluded list from the output
            exclusion_list.extend([k for k in keys if not (k == "esc" or k in exclusion_list or self.D[n][c][k] == 0)])

            # instruct decoder to decrement order and repeat
            return False, exclusion_list, "esc"
        # if PPM found the correct byte:
        else:
            # add symbol to output symbols
            self.output.append(int(symbol))

            # instruct decoder that correct symbol has been find
            return True, [], symbol

    def order_minus1_update(self):
        tag = int(self.binary_tag, 2)

        frequency = (((tag - self.low + 1) * self.max_freq) - 1) / (self.high - self.low + 1)
        print("frequency = {}".format(frequency))

        bound = 0
        while self.freq_table[bound] <= frequency and bound < self.max_freq:
            bound += 1

        if bound >= self.max_freq:
            print("Decoding frequency bound not found")
            exit(1)

        low_prev = self.low
        high_prev = self.high

        self.low = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[bound - 1]) / self.max_freq)
        self.high = low_prev + math.floor(((high_prev - low_prev + 1) * self.freq_table[bound]) / self.max_freq) - 1

        print("found bound = [{}, {})".format(bound - 1, bound))

        symbol = bound - 1
        self.output.append(symbol)

        return symbol

    def process_lht(self):

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

    def backtrack_update(self, current_position, n, symb):
        # NOTE: when adding new symbols, remember to convert to a string as its a byte
        print("\nBACKTRACKING TO UPDATE D:")
        print("   CURRENT VARS: pos = {}, symb = {}, output = {}".format(current_position, symb, self.output))
        n = max(n, 0)
        current_output = self.output[:-1]

        while n <= self.N:
            # find corresponding context to current order
            if n == 0:
                c = '[]'
                print("   ZERO: order = {}, context = {}".format(n, c))
            elif len(current_output) <= n:
                byts = ["-"] * (n - len(current_output))
                byts.extend(current_output)
                c = str(byts)
                print("   MADE: order = {}, context = {}".format(n, c))
            else:
                c = str(current_output[-n:])
                print("   READ: order = {}, context = {}".format(n, c))

            # update count of context-symbol in D
            if c in self.D[n].keys():
                if symb in self.D[n][c].keys():
                    if self.D[n][c][symb] == 0:
                        # if the symbol exists but is zero increment esc count (PPM method B) as well as symbol count
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
        self.high = 1024
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

decoder = PPMDecoder()
message, info = decoder.full_decoding(encoding)
print()
decoder.printD()

print("Input sequence:", encoding)
print("Input file size:", info[0])
print("Output file size:", info[1])
print("Output sequence:", message)

with open(file_name + "-decoded.tex", 'wb') as f:
    f.write(message)
