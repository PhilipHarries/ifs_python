""" image functionality of ifs """
import numpy_ifs
import numpy


class MalformedImageError(Exception):
    """ error class for IFSImage """

    def __str__(self):
        return "Malformed Image!"


class BadRangeSizeError(Exception):
    """ error class for IFSImage """

    def __str__(self):
        return "Bad range size!"


class BadDomainSizeError(Exception):
    """ error class for IFSImage """

    def __str__(self):
        return "Bad domain size!"


class OutOfArrayError(Exception):
    """ error class for IFSImage """

    def __init__(self, value):
        self.value = value
        Exception.__init__(self)

    def __str__(self):
        if self.value is None:
            return "Requested value that is out of array!"
        else:
            return "value is outside array! (" + self.value + ")"


class NullValueError(Exception):
    """ error class for IFSImage """

    def __str__(self):
        return "Null value in array!"


class IFSImage(object):
    """ base image object for IFS """

    def __init__(self, width, whiteval, range_size, domain_size, data):
        self.width = width
        self.length = len(data)
        self.height = self.length / self.width
        self.whiteval = whiteval
        self.range_size = range_size
        self.domain_size = domain_size
        if self.length % width != 0:
            raise MalformedImageError
        if (self.length % self.range_size != 0 or self.height % self.range_size != 0 or
                self.range_size > self.width or self.range_size > self.height):
            raise BadRangeSizeError
        if self.domain_size > self.width or self.domain_size > self.height:
            raise BadDomainSizeError
        self.width_in_ranges = self.width / self.range_size
        self.height_in_ranges = self.height / self.range_size
        self.width_in_domains = self.width + 1 - self.domain_size
        self.height_in_domains = self.height + 1 - self.domain_size
        self.num_ranges = self.width_in_ranges * self.height_in_ranges
        self.num_domains = self.width_in_domains * self.height_in_domains
        self.ranges = [None] * self.num_ranges
        self.domains = [None] * self.num_domains
        self.height = self.length / width
        self.data = numpy.array(list(data)).reshape(self.height, self.width)

    # def __str__(self):
    #     r_str = ""
    #     for tracker in range(self.length):
    #         if (tracker + 1) % self.width == 0:
    #             if (tracker + 1) % self.length == 0:
    #                 r_str += str(self.data[tracker])
    #             else:
    #                 r_str += str(self.data[tracker]) + ",\n"
    #         else:
    #             r_str += str(self.data[tracker]) + ", "
    #     return r_str

    def write_pgm(self, filename):
        """ write pgm """
        with open(filename, 'w') as wfile:
            wfile.write("P2\n")
            wfile.write("# ifs compressor\n")
            wfile.write(str(self.width) + " " + str(self.height) + "\n")
            wfile.write(str(self.whiteval) + "\n")
            for val in self.data.flatten().tolist():
                if val < 0:
                    wfile.write("0\n")
                elif val > self.whiteval:
                    wfile.write(str(self.whiteval) + "\n")
                else:
                    wfile.write(str(val) + "\n")

    def get_range(self, i, j=None):
        """ return a given range """
        if j is None:
            if self.ranges[i] is not None:
                return self.ranges[i]
            else:
                x_range_coord = i % self.width_in_ranges
                y_range_coord = i / self.width_in_ranges
                self.ranges[i] = self.get_range(x_range_coord, y_range_coord)
                return self.ranges[i]
        else:
            x_coord = i * self.range_size
            y_coord = j * self.range_size
            return self.get_square_submatrix(x_coord, y_coord, self.range_size)

    def put_range(self, new_range, i, j=None):
        """ set a given range into image """
        if j is None:
            x_range_coord = i % self.width_in_ranges
            y_range_coord = i / self.width_in_ranges
            try:
                self.put_range(new_range, x_range_coord, y_range_coord)
            except OutOfArrayError as e:
                print "tried to put range " + str(i)
                raise e
        else:
            x_coord = i * self.range_size
            y_coord = j * self.range_size
            self.put_square_submatrix(x_coord, y_coord, new_range)

    def get_ranges(self, start=None):
        """ return an iterator over all ranges """
        if start is None:
            start = 0
        for count in xrange(start, self.num_ranges):
            yield self.get_range(count)

    def get_domains(self):
        """ return an iterator over all domains """
        for count in xrange(self.num_domains):
            try:
                yield self.get_domain(count)
            except OutOfArrayError as e:
                print "failed to get domain " + str(count)
                raise e

    def get_domain(self, i, j=None, decoding=False):
        """ return a given domain """
        if j is None:
            if i < 0 or i > self.num_domains:
                raise OutOfArrayError("requested value " + i + " + is not in the range (0 - " + str(self.num_domains) + ")")
            if self.domains[i] is not None and not decoding:
                return self.domains[i]
            else:
                x_domain_coord = i % self.width_in_domains
                y_domain_coord = i / self.width_in_domains
                if not decoding:
                    self.domains[i] = self.get_domain(x_domain_coord, y_domain_coord)
                    return self.domains[i]
                else:
                    return self.get_domain(x_domain_coord, y_domain_coord)

        else:
            return self.get_square_submatrix(i, j, self.domain_size)

    def get_square_submatrix(self, x, y, size):
        """ get any square submatrix """
        if (size + x > self.width or size + y > self.height or x < 0 or y < 0):
            print "requested size " + str(size) + " + x " + str(x) + " = " + str(size + x)
            print "requested size " + str(size) + " + y " + str(y) + " = " + str(size + y)
            print "in array matrix of width " + str(self.width) + " and height " + str(self.height)
            raise OutOfArrayError("requested a square submatrix that overlaps the edge of image array!")
        data = [None] * (size * size)
        for i in range(size):
            for j in range(size):
                received_value = self.get_value(x + i, y + j)
                if received_value is None:
                    raise NullValueError
                else:
                    data[j * size + i] = self.get_value(x + i, y + j)
        return numpy_ifs.IFSMatrix(size, numpy.array(data).reshape(size, size))

    def put_square_submatrix(self, x, y, new_matrix):
        """ put any square submatrix """
        if (new_matrix.width + x > self.width or new_matrix.height + y > self.height or x < 0 or y < 0):
            print "tried to put new matrix of width " + str(new_matrix.width) + " to x value " + str(x) + " which extends to " + str(new_matrix.width + x)
            print "tried to put new matrix of height " + str(new_matrix.height) + " to y value " + str(y) + " which extends to " + str(new_matrix.width + y)
            print "in array matrix of width " + str(self.width) + " and height " + str(self.height)
            raise OutOfArrayError("tried to put a square submatrix that overlaps the edge of image array!")
        for i in xrange(new_matrix.width):
            for j in xrange(new_matrix.height):
                self.set_value(new_matrix.data.item(j * new_matrix.width + i), x + i, y + j)

    def get_value(self, x, y=None):
        """ get any value """
        if y is None:
            return self.data.item(x)
        else:
            return self.data.item(y, x)
            # return self.get_value(y * self.width + x)

    def set_value(self, value, x, y=None):
        """ get any value """
        if value is not None:
            if y is None:
                numpy.put(self.data, x, value)
                # self.data[x] = value
            else:
                self.set_value(value, y * self.width + x)
        else:
            print "Tried to put null value!"
            raise NullValueError

    def apply_ifs(self, range_num, (domain_num, transform_num, contrast, brightness)):
        """ apply an ifs from domain to range """
        # print "range num is " + str(range_num)
        # print "domain num is " + str(domain_num)
        # print "transform num is " + str(transform_num)
        # print "contrast is " + str(contrast)
        # print "brightness is " + str(brightness)
        # print "domain is " + str(self.get_domain(domain_num))
        self.put_range(numpy_ifs.apply_transform(transform_num,
                                           self.get_domain(domain_num, decoding=True)
                                           .resize(self.range_size, self.range_size)
                                           .adjust_contrast(contrast)
                                           .adjust_brightness(brightness)),
                       range_num)
