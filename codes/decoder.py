import sys
import os
import math
import pickle


class PPMDecoder:
    def __init__(self, max_freq=256):
        self.max_freq = max_freq
        self.m = 10
        self.e3 = 0

        self.low = 0
        self.high = 0
        for h in range(self.m):
            self.high += 2 ** h

        self.N = 6
        self.D = [{} for _ in range(self.N + 1)]
        self.freq_table = self.make_freq_table()

        self.start = 0
        self.full_tag = ''
        self.binary_tag = ''
        self.int_tag = 0
        self.EOF = False
        self.output = []

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

    def extract_m(self, full_tag):
        self.m = int(full_tag[:8], 2)
        self.full_tag = full_tag[8:]

        self.high = 0
        for h in range(self.m):
            self.high += 2 ** h

    def decode(self, input_tag):
        self.extract_m(input_tag)

        self.binary_tag = self.full_tag[:self.m]
        self.int_tag = int(self.binary_tag, 2)
        byte_count = 0

        while self.binary_tag != '' and self.EOF is False:

            byte_count += 1
            order = self.N
            excluded = []
            # print("\nBYTE NO. =", byte_count)

            while order > -2:
                # print("ORDER =", order)
                if order > -1:
                    # find corresponding context to current order
                    if len(self.output) < order:
                        byts = ["-"] * (order - len(self.output))
                        byts.extend(self.output)
                        context = str(byts)
                        # print("made context =", context)
                    else:
                        context = str(self.output[byte_count - order - 1:])
                        # print("existing context =", context)

                    # search current order for that context
                    # if not found:
                    if context not in self.D[order].keys():
                        # no need to update self.low and self.high on this esc as low_prob = 0.0 and high_prob = 1.0
                        # decrement order and repeat
                        # print("context not in D[{}]".format(order))
                        order -= 1
                    # if found:
                    else:
                        # print("found context: D[{}][{}] = {}".format(order, context, self.D[order][context]))

                        # check if corresponding table row contains any non-zero entries
                        sum_values = sum([self.D[order][context][k] for k in self.D[order][context].keys() if k not in excluded])

                        # if no no-zero entries:
                        if sum_values == 0:
                            # no need to update self.low and self.high on this esc as low_prob = 0.0 and high_prob = 1.0
                            # decrement order and repeat
                            # print("no non-zero entries in D[{}]".format(order))
                            order -= 1
                        # if there are non-zero entries:
                        else:
                            # print("2) non-zero context values found in D[{}]: sum_values = {}, excluded = {}".format(order, sum_values, excluded))

                            found, excluded, symbol = self.ppm_update(sum_values, order, context, excluded)
                            self.process_lht()

                            # if PPM found the correct byte:
                            if found:
                                # print("Found byte = {}".format(symbol))
                                # backtrack update PPM table orders n -> self.N given seen contexts/symbol
                                self.backtrack_update(byte_count, order, str(symbol))

                                if symbol == 4:
                                    # print("\nFOUND EOF, BREAKING\n")
                                    self.EOF = True
                                    self.output = self.output[:-1]

                                break
                            # otherwise, if symbol is esc:
                            else:
                                # decrement order and repeat
                                # print("Byte not found, symbol = 'esc'")
                                order -= 1
                # if order == -1:
                else:
                    # do normal AC to get symbol/updates
                    symbol = self.order_minus1_update()
                    self.process_lht()

                    # print("decoding in order -1, found byte = {}, type = {}".format(symbol, type(symbol)))
                    if not (0 <= int(symbol) < 256):
                        print("\nERROR, decoded symbol invalid:", symbol)
                        exit(1)

                    # backtrack update PPM table orders 0 -> self.N given seen contexts/symbol
                    self.backtrack_update(byte_count, order, str(symbol))

                    if symbol == 4:
                        # print("\nFOUND EOF, BREAKING\n")
                        self.EOF = True
                        self.output = self.output[:-1]

                    break

            # print("CURRENT OUTPUT =", repr(bytes(self.output)))

            # print("self.output = {}".format(self.output))

        self.output = bytes(self.output)

        return self.output

    def ppm_update(self, sum_values, n, c, exclusion_list):
        self.int_tag = int(self.binary_tag, 2)

        # calculate frequency value (based on sum of non-zero entries)
        frequency = (((self.int_tag - self.low + 1) * sum_values) - 1) / (self.high - self.low + 1)
        # print("frequency = ((({} - {} + 1) * {}) - 1) / ({} - {} + 1) = {}".format(self.int_tag, self.low, sum_values, self.high, self.low, frequency))

        # find low prob and high prob using PPM table, and associated symbol
        keys = [k for k in self.D[n][c].keys() if k not in exclusion_list]
        j = 0
        low_bound = 0
        high_bound = self.D[n][c][keys[0]]

        # print("searching table: D[{}][{}] = {}".format(n, c, self.D[n][c]))

        while frequency >= high_bound:
            j += 1
            low_bound = high_bound
            high_bound += self.D[n][c][keys[j]]

        # print("found bound = [{}, {}), j= {}".format(low_bound, high_bound, j))

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
            if not (0 <= int(symbol) < 256):
                print("\nERROR, decoded symbol invalid:", symbol)
                exit(1)
            else:
                # add symbol to output symbols
                self.output.append(int(symbol))

                # instruct decoder that correct symbol has been find
                return True, [], symbol

    def order_minus1_update(self):
        self.int_tag = int(self.binary_tag, 2)

        frequency = (((self.int_tag - self.low + 1) * self.max_freq) - 1) / (self.high - self.low + 1)
        # print("frequency = {}".format(frequency))

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

        # print("found bound = [{}, {})".format(bound - 1, bound))

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
        # print("BACKTRACKING TO UPDATE D")
        n = max(n, 0)
        current_output = self.output[:-1]

        while n <= self.N:
            # find corresponding context to current order
            if n == 0:
                c = '[]'
            elif len(current_output) <= n:
                byts = ["-"] * (n - len(current_output))
                byts.extend(current_output)
                c = str(byts)
            else:
                c = str(current_output[-n:])

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

    def reset(self):
        self.e3 = 0
        self.low = 0
        self.start = 0
        self.int_tag = 0
        self.full_tag = ''
        self.binary_tag = ''
        self.output = []
        self.EOF = False

        self.high = 0
        for h in range(self.m):
            self.high += 2 ** h

    def full_decoding(self, sequence):
        decoding = self.decode(sequence)
        data = self.output_data(sequence, decoding)
        self.reset()

        return decoding, data


file = sys.argv[1]
file_name, extension = os.path.splitext(file)
print("File name: ", file_name)

if extension != ".lz":
    print("Not a compatible compressed file!")
    exit(1)

with open(file, 'rb') as f:
    encoding = pickle.load(f)

# print("Encoding:", encoding[:25])
# print("Type:", type(encoding))

decoder = PPMDecoder()
message, info = decoder.full_decoding(encoding)

# print("Input sequence:", encoding)
# print("Input file size:", info[0])
# print("Output file size:", info[1])
# print("Output sequence:", message)

with open(file_name + "-decoded.tex", 'wb') as f:
    f.write(message)

print("\nDECODING COMPLETE!!\n")
