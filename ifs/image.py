""" image functionality of ifs """
# import math
import ifs


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

    def __str__(self):
        return "Requested value that is out of array!"


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
        self.height_in_domains = self.width + 1 - self.domain_size
        self.num_ranges = self.width_in_ranges * self.height_in_ranges
        self.num_domains = self.width_in_domains * self.height_in_domains
        self.ranges = [None] * self.num_ranges
        self.domains = [None] * self.num_domains
        self.height = self.length / width
        self.data = list(data)

    def __str__(self):
        r_str = ""
        for tracker in range(self.length):
            if (tracker + 1) % self.width == 0:
                if (tracker + 1) % self.length == 0:
                    r_str += str(self.data[tracker])
                else:
                    r_str += str(self.data[tracker]) + ",\n"
            else:
                r_str += str(self.data[tracker]) + ", "
        return r_str

    def write_pgm(self, filename):
        """ write pgm """
        with open(filename, 'w') as wfile:
            wfile.write("P2\n")
            wfile.write("# ifs compressor\n")
            wfile.write(str(self.width) + " " + str(self.height) + "\n")
            wfile.write(str(self.whiteval) + "\n")
            for val in self.data:
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
            self.put_range(new_range, x_range_coord, y_range_coord)
        else:
            x_coord = i * self.range_size
            y_coord = j * self.range_size
            self.put_square_submatrix(x_coord, y_coord, new_range)

    def get_ranges(self):
        """ return an iterator over all ranges """
        for count in xrange(self.num_ranges):
            yield self.get_range(count)

    def get_domains(self):
        """ return an iterator over all domains """
        for count in xrange(self.num_domains):
            yield self.get_domain(count)

    def get_domain(self, i, j=None, decoding=False):
        """ return a given domain """
        if j is None:
            if i < 0 or i > self.num_domains:
                raise OutOfArrayError
            if self.domains[i] is not None and not decoding:
                return self.domains[i]
            else:
                x_domain_coord = i % self.width_in_domains
                y_domain_coord = i / self.height_in_domains
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
            raise OutOfArrayError
        data = [None] * (size * size)
        for i in range(size):
            for j in range(size):
                received_value = self.get_value(x + i, y + j)
                if received_value is None:
                    raise NullValueError
                else:
                    data[j * size + i] = self.get_value(x + i, y + j)
        return ifs.IFSMatrix(size, data)

    def put_square_submatrix(self, x, y, new_matrix):
        """ put any square submatrix """
        if (new_matrix.width + x > self.width or new_matrix.height + y > self.height or x < 0 or y < 0):
            raise OutOfArrayError
        for i in xrange(new_matrix.width):
            for j in xrange(new_matrix.height):
                self.set_value(new_matrix.data[j * new_matrix.width + i], x + i, y + j)

    def get_value(self, x, y=None):
        """ get any value """
        if y is None:
            return self.data[x]
        else:
            return self.get_value(y * self.width + x)

    def set_value(self, value, x, y=None):
        """ get any value """
        if value is not None:
            if y is None:
                self.data[x] = value
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
        self.put_range(ifs.apply_transform(transform_num,
                                           self.get_domain(domain_num, decoding=True)
                                           .resize(self.range_size, self.range_size)
                                           .adjust_contrast(contrast)
                                           .adjust_brightness(brightness)),
                       range_num)
