""" matrix functionality of ifs """
import math


class MalformedIFSMatrixError(Exception):
    """ error class for IFSMatrix """

    def __str__(self):
        return "Malformed IFS Matrix!"


class BadComparisonError(Exception):
    """ error class for IFSMatrix """

    def __str__(self):
        return "IFS Matrices of different size!"


class IFSMatrix(object):
    """ base matrix object for IFS """

    def __init__(self, width, data):
        self.width = width
        self.length = len(data)
        if self.length % width != 0:
            raise MalformedIFSMatrixError
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

    def identity(self):
        """ identity is simple copy """
        new_data = list(self.data)
        return IFSMatrix(self.width, new_data)

    def rotate180(self):
        """ rotate180 which is a simple reverse """
        new_data = list(self.data)
        new_data.reverse()
        return IFSMatrix(self.width, new_data)

    def reflect_in_y(self):
        """ reflect_in_y is a reverse of each row """
        new_data = list(self.data)
        for j in range(self.height):
            for i in range(self.width):
                new_data[coord_to_index(i, j, self.width)] = (self.data[coord_to_index(self.width - 1 - i, j, self.width)])
        return IFSMatrix(self.width, new_data)

    def reflect_in_leading_diag(self):
        """ reflect in \\ """
        new_data = list(self.data)
        for j in range(self.height):
            for i in range(self.width):
                new_data[coord_to_index(j, i, self.height)] = self.data[coord_to_index(i, j, self.width)]
        return IFSMatrix(self.height, new_data)

    def reflect_in_x(self):
        """ reflect_in_x  """
        return self.reflect_in_y().rotate180()

    def reflect_in_contra_diag(self):
        """ reflect_in_contra_diag """
        return self.reflect_in_leading_diag().rotate180()

    def rotate270(self):
        """ rotate270 """
        return self.reflect_in_leading_diag().reflect_in_x()

    def rotate90(self):
        """ rotate90 """
        return self.reflect_in_leading_diag().reflect_in_y()

    def sum_vals(self):
        """ total all the values in data """
        total = 0
        for val in self.data:
            total += val
        return total

    def sum_sqr_vals(self):
        """ total all the squares of values in data """
        total = 0
        for val in self.data:
            total += val * val
        return total

    def adjust_contrast(self, contrast):
        """ add contrast level to all values in data """
        new_data = [None] * self.length
        for count in xrange(self.length):
            new_data[count] = int(round(float(self.data[count]) * contrast))
        return IFSMatrix(self.width, new_data)

    def adjust_brightness(self, brightness):
        """ add brightness level to all values in data """
        new_data = [None] * self.length
        for count in xrange(self.length):
            new_data[count] = int(round(self.data[count] + brightness))
        return IFSMatrix(self.width, new_data)

    def resize(self, new_length, new_height=None):
        """ extend or contract to new_length, new_height """
        if new_height is None:
            return self.resize(new_length, new_length)
        new_data = []
        for row in list_split(self.data, self.width):
            new_row = resize(row, new_length)
            new_data.append(new_row)
        tMatrix = IFSMatrix(new_length, list(flatten(new_data)))
        tMatrix = IFSMatrix(tMatrix.height, tMatrix.rotate270().data)
        new_data = []
        for row in list_split(tMatrix.data, tMatrix.width):
            new_row = resize(row, new_height)
            new_data.append(new_row)
        tMatrix = IFSMatrix(new_height, list(flatten(new_data)))
        tMatrix = IFSMatrix(new_length, tMatrix.rotate90().data)
        return tMatrix


def diff_ifs_matrices(matrix_a, matrix_b):
    """ calculate a numeric difference between two matrices """
    if matrix_a.length != matrix_b.length or matrix_a.width != matrix_b.width:
        print str(matrix_a.length)
        print str(matrix_b.length)
        print str(matrix_a.width)
        print str(matrix_b.width)
        raise BadComparisonError
    diff = 0
    for count in xrange(matrix_a.length):
        this_diff = matrix_a.data[count] - matrix_b.data[count]
        diff += this_diff * this_diff
    return diff


def find_best_transform(range_matrix, domain_matrix):
    """ calculates best fit transform for a domain to match a given range """
    if range_matrix.length != domain_matrix.length or range_matrix.width != domain_matrix.width:
        raise BadComparisonError
    best_fit_value = 9999999999
    best_transform = None
    best_contrast = None
    best_brightness = None
    data = [0] * range_matrix.length
    transformed_domain = IFSMatrix(range_matrix.width, data)
    for transform_num in xrange(8):
        transformed_domain = apply_transform(transform_num, domain_matrix)
        contrast = calculate_contrast(range_matrix, transformed_domain)
        brightness = calculate_brightness(range_matrix, transformed_domain, contrast)
        transformed_domain = transformed_domain.adjust_contrast(contrast)
        transformed_domain = transformed_domain.adjust_brightness(brightness)
        fit_value = diff_ifs_matrices(range_matrix, transformed_domain)
        fit_threshold = range_matrix.length * 1
        if fit_value < fit_threshold:
            return (transform_num, contrast, brightness, fit_value)
        elif fit_value < best_fit_value:
            best_fit_value = fit_value
            best_transform = transform_num
            best_contrast = contrast
            best_brightness = brightness
    return (best_transform, best_contrast, best_brightness, best_fit_value)


def apply_transform(transform_num, matrix):
    """ applies a given transform to a matrix """
    # apply transforms in order of complexity, with the hope of finding a great fit early
    if transform_num == 0:
        return matrix.identity()
    if transform_num == 1:
        return matrix.rotate180()
    if transform_num == 2:
        return matrix.reflect_in_y()
    if transform_num == 3:
        return matrix.reflect_in_x()
    if transform_num == 4:
        return matrix.reflect_in_leading_diag()
    if transform_num == 5:
        return matrix.reflect_in_contra_diag()
    if transform_num == 6:
        return matrix.rotate270()
    if transform_num == 7:
        return matrix.rotate90()
    return None


def calculate_contrast(range_matrix, domain_matrix):
    """ calculates required contrast change to domain to approximate range """
    if range_matrix.length != domain_matrix.length or range_matrix.width != domain_matrix.width:
        raise BadComparisonError
    sum_rd = 0
    for count in xrange(range_matrix.length):
        sum_rd += range_matrix.data[count] * domain_matrix.data[count]
    divisor = ((float(range_matrix.length) * float(domain_matrix.sum_sqr_vals())) - (float(domain_matrix.sum_vals()) * float(domain_matrix.sum_vals())))
    if divisor == 0:
        contrast = 0.0
    else:
        contrast = (((float(domain_matrix.length) * float(sum_rd)) - (float(domain_matrix.sum_vals()) * float(range_matrix.sum_vals()))) / float(divisor))
    return contrast


def calculate_brightness(range_matrix, domain_matrix, contrast):
    """ calculates required brightness change to domain to approximate range for given contrast """
    if range_matrix.length != domain_matrix.length or range_matrix.width != domain_matrix.width:
        raise BadComparisonError
    # print "calculating brightness"
    # print "sumD:     " + str(domain_matrix.sum_vals())
    # print "sumR:     " + str(range_matrix.sum_vals())
    # print "n:        " + str(range_matrix.length)
    # print "contrast: " + str(contrast)
    # print "brightness = ( sumD - contrast * sumR ) / n"
    # print("brightness = " + str(float(range_matrix.sum_vals())) + " - (" + str(float(contrast)) + " * " +
    #      str(domain_matrix.sum_vals()) + ") / " + str(float(range_matrix.length)))
    brightness = (float(range_matrix.sum_vals()) - (float(contrast * domain_matrix.sum_vals()))) / float(range_matrix.length)
    # print "brightness: " + str(brightness)
    return brightness


def flatten(a_list):
    """ flatten a list (one nested layer) """
    for item in a_list:
        if isinstance(item, (list, tuple)):
            for another_item in item:
                yield another_item
        else:
            yield item


def coord_to_index(x_coord, y_coord, width):
    """ translate an (x, y) coord to an index """
    return y_coord * width + x_coord


def list_split(a_list, sublength):
    """ yield successive lists of length sublength """
    for i in xrange(0, len(a_list), sublength):
        yield a_list[i:i + sublength]


def resize(a_list, new_length):
    """ stretch or shrink the list, interpolating values """
    new_list = [None] * new_length
    if len(a_list) == new_length:
        new_list = list(a_list)
    elif new_length < len(a_list):
        if len(a_list) % new_length == 0:
            # exact integer division
            # print "doing exact integer division!"
            new_list = []
            scaling_factor = len(a_list) / new_length
            for sub_list in list_split(a_list, scaling_factor):
                new_list.append(sum(sub_list) / scaling_factor)
        else:
            scaling_factor = float(new_length) / len(a_list)
            for new_coord in range(new_length):
                mapped_coord = (float(new_coord) / scaling_factor)
                lower_mapped_coord = int(math.floor(mapped_coord))
                upper_mapped_coord = int(math.ceil(mapped_coord))
                coord_range = upper_mapped_coord - lower_mapped_coord
                if coord_range == 0:
                    new_list[new_coord] = a_list[int(mapped_coord)]
                else:
                    lower_val_proportion = (mapped_coord - lower_mapped_coord) / coord_range
                    upper_val_proportion = (upper_mapped_coord - mapped_coord) / coord_range
                    lower_val = a_list[lower_mapped_coord]
                    upper_val = a_list[upper_mapped_coord]
                    aggregate_val = (lower_val_proportion * lower_val) + (upper_val_proportion * upper_val)
                    new_list[new_coord] = int(round(aggregate_val))
    else:
        if new_length % len(a_list) == 0:
            # exact integer expansion
            # print "doing exact integer expansion!"
            scaling_factor = new_length / len(a_list)
            for i in xrange(new_length):
                new_list.append(a_list[i / scaling_factor])
        else:
            scaling_factor = float(new_length) / len(a_list)
            for new_coord in range(new_length):
                mapped_coord = (float(new_coord) / scaling_factor)
                lower_mapped_coord = int(math.floor(mapped_coord))
                upper_mapped_coord = int(math.ceil(mapped_coord))
                coord_range = upper_mapped_coord - lower_mapped_coord
                if coord_range == 0:
                    new_list[new_coord] = a_list[int(mapped_coord)]
                else:
                    lower_val_proportion = (mapped_coord - lower_mapped_coord) / coord_range
                    upper_val_proportion = (upper_mapped_coord - mapped_coord) / coord_range
                    lower_val = a_list[lower_mapped_coord]
                    try:
                        upper_val = a_list[upper_mapped_coord]
                    except Exception:
                        upper_val = a_list[lower_mapped_coord]
                    aggregate_val = (lower_val_proportion * lower_val) + (upper_val_proportion * upper_val)
                    new_list[new_coord] = int(round(aggregate_val))
    return new_list
