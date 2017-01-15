""" run ifs """
import random
import os
import sys
import optparse
import ifs


class InvalidFileFormatError(Exception):
    """ error class for IFS """

    def __str__(self):
        return "Invalid file format!"


def read_pgm(filename):
    """ read pgm data from a file """
    with open(filename, 'r') as image_file:
        line_count = 0
        data = []
        for line in image_file:
            line = line.rstrip('\n')
            if line_count == 0:
                if line != "P2":
                    raise InvalidFileFormatError
            elif line_count == 1:
                pass
            elif line_count == 2:
                (width, height) = line.split(" ")
            elif line_count == 3:
                whiteval = line
            else:
                data.append(line)
            line_count += 1
        return (width, height, whiteval, data)


def read_ifs(filename):
    """ read ifs data from a file """
    width = None
    height = None
    range_size = None
    domain_size = None
    whiteval = None
    data = []
    with open(filename, 'r') as ifs_file:
        line_count = 0
        for line in ifs_file:
            line = line.rstrip('\n')
            if line_count == 0:
                if line != "#IFS":
                    raise InvalidFileFormatError
            elif line_count == 1:
                (width, height, range_size, domain_size, whiteval) = line.split(" ")
                width = int(width)
                height = int(height)
                range_size = int(range_size)
                domain_size = int(domain_size)
                whiteval = int(whiteval)
            else:
                (dom, tra, con, bri) = line.split(" ")
                dom = int(dom)
                tra = int(tra)
                con = float(con)
                bri = float(bri)
                data.append((dom, tra, con, bri))
            line_count += 1
    if (width is None or height is None or whiteval is None or
            range_size is None or domain_size is None or
            data == []):
        raise InvalidFileFormatError
    return (width, height, range_size, domain_size, whiteval, data)


def write_ifs(filename, width, height, whiteval, range_size, domain_size, ifs_data):
    """ write encoded ifs data to a file """
    print "writing " + filename
    with open(filename, 'w') as ifs_file:
        ifs_file.write("#IFS\n")
        ifs_file.write(str(width) + " " + str(height) + " " +
                       str(range_size) + " " + str(domain_size) + " " +
                       str(whiteval) + "\n")
        for ifs_info in ifs_data:
            ifs_file.write(str(ifs_info[0]) + " " +
                           str(ifs_info[1]) + " " +
                           str(ifs_info[2]) + " " +
                           str(ifs_info[3]) + "\n")


def main():
    """ main function """
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file', action='store', type='string', help='the pgm file you wish to encode')
    parser.add_option('-r', '--rangesize', action='store', type='int', default=4, help='the required rangesize')
    parser.add_option('-d', '--domainsize', action='store', type='int', default=8, help='the required domainsize')
    parser.add_option('-i', '--iterations', action='store', type='int', default=None, help='the number of times to apply ifs during decoding')
    parser.add_option('-p', '--print_intervals', action='store', type='int', default=0, help='the number of times to print interim versions of the generated image')
    options, _ = parser.parse_args()
    in_file = "input/" + options.file
    range_size = options.rangesize
    domain_size = options.domainsize
    ifs_file = "encoded_files/" + in_file.lstrip("input/").rstrip(".pgm") + "_r" + str(range_size) + "_d" + str(domain_size) + ".ifs"
    out_file = "output/" + ifs_file.lstrip("encoded_files/").rstrip(".ifs") + ".pgm"

    print "range size " + str(range_size)
    print "domain size " + str(domain_size)

    if not os.path.exists(ifs_file):
        print "opening image " + in_file
        (width, height, whiteval, data) = read_pgm(in_file)
        print "done"
        width = int(width)
        height = int(width)
        whiteval = int(whiteval)
        for i in xrange(len(data)):
            data[i] = int(data[i])
        fit_threshold = 0  # float(range_size) * 0.001
        image = ifs.IFSImage(width, whiteval, range_size, domain_size, data)
        ifs_array = []
        resized_domain_array = [None] * image.num_domains

        print "calculating best ifs transform for each range"
        current_range = 0
        for irange in image.get_ranges():
            best_domain = None
            best_transform = None
            best_contrast = None
            best_brightness = None
            best_fit = 9999999999
            domain_num = 0
            for domain in image.get_domains():
                if resized_domain_array[domain_num] is None:
                    resized_domain_array[domain_num] = domain.resize(range_size)
                (transform, contrast, brightness, fit) = ifs.find_best_transform(irange, resized_domain_array[domain_num])
                if fit < best_fit:
                    best_fit = fit
                    best_domain = domain_num
                    best_transform = transform
                    best_contrast = contrast
                    best_brightness = brightness
                if fit <= fit_threshold:
                    break
                domain_num += 1
            try:
                if (current_range + 1) % (image.num_ranges / 10) == 0:
                    sys.stdout.write('%')
            except ZeroDivisionError:
                pass
            sys.stdout.flush()
            ifs_array.append((best_domain, best_transform, best_contrast, best_brightness))
            current_range += 1

        write_ifs(ifs_file, width, height, whiteval, range_size, domain_size, ifs_array)
    else:
        (width, height, range_size, domain_size, whiteval, ifs_array) = read_ifs(ifs_file)

    seed_data = [128] * width * height
    working_image = ifs.IFSImage(width, whiteval, range_size, domain_size, seed_data)

    if options.iterations is None:
        num_ifs_to_apply = working_image.num_ranges * 32
    else:
        num_ifs_to_apply = options.iterations

    if options.print_intervals != 0:
        temp_file_dir = out_file.rstrip(".pgm")
        if not os.path.isdir(temp_file_dir):
            os.mkdir(temp_file_dir)

    test_sample_interval = 128
    test_image_data = list(working_image.data)
    for i in range(num_ifs_to_apply):
        range_num = random.randrange(len(ifs_array))
        working_image.apply_ifs(range_num, ifs_array[range_num])
        if options.print_intervals != 0:
            if i % options.print_intervals == 0:
                temp_out_file = temp_file_dir + "/" + out_file.lstrip("output/").rstrip(".pgm") + "_i" + str(i) + ".pgm"
                working_image.write_pgm(temp_out_file)
        if (i + 1) % test_sample_interval == 0:
            match = True
            for j in range(len(working_image.data)):
                if working_image.data[j] != test_image_data[j]:
                    match = False
                    break
            if match:
                print "Exiting loop as ifs has converged"
                temp_out_file = temp_file_dir + "/" + out_file.lstrip("output/").rstrip(".pgm") + "_i" + str(i) + ".pgm"
                working_image.write_pgm(temp_out_file)
                break
            else:
                test_image_data = list(working_image.data)

    working_image.write_pgm(out_file)


main()
