import sys
import os
import math


class PPMDecoder:
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

        self.start = 0
        self.full_tag = ''
        self.binary_tag = ''
        self.int_tag = 0
        self.EOF = False
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

    def make_freq_table(self, s=0.5):
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

    def convert_to_bits(self, byte_array):
        for byte in byte_array:
            bit = format(byte, 'b').zfill(8)
            self.full_tag += bit

    def extract_m(self, full_tag):
        self.convert_to_bits(full_tag)
        self.m = int(self.full_tag[:8], 2)
        self.full_tag = self.full_tag[8:]

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

            while order > -2:
                if order > -1:
                    # find corresponding context to current order
                    if len(self.output) < order:
                        char_list = [116, 104, 101, 32, 116, 104]
                        byts = char_list[:order - len(self.output)]

                        byts.extend(self.output)
                        context = str(byts)
                    else:
                        context = str(self.output[byte_count - order - 1:])

                    # search current order for that context
                    # if not found:
                    if context not in self.D[order].keys():
                        # no need to update self.low and self.high on this esc as low_prob = 0.0 and high_prob = 1.0
                        # decrement order and repeat
                        order -= 1
                    # if found:
                    else:
                        # check if corresponding table row contains any non-zero entries
                        sum_values = sum([self.D[order][context][k] for k in self.D[order][context].keys() if k not in excluded])

                        # if no no-zero entries:
                        if sum_values == 0:
                            # no need to update self.low and self.high on this esc as low_prob = 0.0 and high_prob = 1.0
                            # decrement order and repeat
                            order -= 1
                        # if there are non-zero entries:
                        else:

                            found, excluded, symbol = self.ppm_update(sum_values, order, context, excluded)
                            self.process_lht()

                            # if PPM found the correct byte:
                            if found:
                                # backtrack update PPM table orders n -> self.N given seen contexts/symbol
                                self.backtrack_update(order, str(symbol), count=byte_count)

                                if symbol == 4:
                                    self.EOF = True
                                    self.output = self.output[:-1]

                                break
                            # otherwise, if symbol is esc:
                            else:
                                # decrement order and repeat
                                order -= 1
                # if order == -1:
                else:
                    # do normal AC to get symbol/updates
                    symbol = self.order_minus1_update()
                    self.process_lht()

                    if not (0 <= int(symbol) < 256):
                        print("\nERROR, decoded symbol invalid:", symbol)
                        exit(1)

                    # backtrack update PPM table orders 0 -> self.N given seen contexts/symbol
                    self.backtrack_update(order, str(symbol), count=byte_count)

                    if symbol == 4:
                        self.EOF = True
                        self.output = self.output[:-1]
                    break

        self.output = bytes(self.output)

        return self.output

    def ppm_update(self, sum_values, n, c, exclusion_list):
        self.int_tag = int(self.binary_tag, 2)

        # calculate frequency value (based on sum of non-zero entries)
        frequency = (((self.int_tag - self.low + 1) * sum_values) - 1) / (self.high - self.low + 1)

        # find low prob and high prob using PPM table, and associated symbol
        keys = [k for k in self.D[n][c].keys() if k not in exclusion_list]
        j = 0
        low_bound = 0
        high_bound = self.D[n][c][keys[0]]

        while frequency >= high_bound:
            j += 1
            low_bound = high_bound
            high_bound += self.D[n][c][keys[j]]

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

    def increment(self, count):
        incr = max(1, math.floor(count / 25000))
        return incr

    def backtrack_update(self, n, symb, count=0):
        n = max(n, 0)
        current_output = self.output[:-1]

        while n <= self.N:
            # find corresponding context to current order
            if n == 0:
                c = '[]'
            elif len(current_output) <= n:
                char_list = [116, 104, 101, 32, 116, 104]
                byts = char_list[:n - len(current_output)]

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

                    increment = self.increment(count)
                    self.D[n][c][symb] += increment
                else:
                    esc_count = self.D[n][c].pop("esc", 0)
                    self.D[n][c][symb] = 0
                    self.D[n][c]["esc"] = esc_count
            else:
                self.D[n][c] = {symb: 0, "esc": 0}

            # increment n
            n += 1

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
        self.reset()

        return decoding


file = sys.argv[1]
file_name, extension = os.path.splitext(file)
# print("File name: ", file_name)

if extension != ".lz":
    print("Not a compatible compressed file!")
    exit(1)

with open(file, 'rb') as file:
    encoding = file.read()

decoder = PPMDecoder()
message = decoder.full_decoding(encoding)

with open(file_name + "-decoded.tex", 'wb') as f:
    f.write(message)
