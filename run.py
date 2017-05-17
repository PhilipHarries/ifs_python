""" run ifs """
import random
import os
import optparse
import datetime
import numpy_ifs
from time import time


class InvalidFileFormatError(Exception):
    """ error class for IFS """

    def __str__(self):
        return "Invalid file format!"


def read_pgm(filename):
    """ read pgm data from a file """
    with open(filename, 'r') as image_file:
        line_count = 0
        data = []
        try:
            for line in image_file:
                line = line.rstrip('\n')
                if line_count == 0:
                    if line != "P2":
                        raise InvalidFileFormatError
                elif line_count == 1:
                    pass
                elif line_count == 2:
                    (width, height) = line.split()
                elif line_count == 3:
                    whiteval = line
                else:
                    for val in line.split():
                        data.append(val)
                line_count += 1
	except ValueError as ve:
            print "Error encountered with the following line!"
            print line
            print ve
            raise ve
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
                try:
                    (dom, tra, con, bri) = line.split()
                    dom = int(dom)
                    tra = int(tra)
                    con = float(con)
                    bri = float(bri)
                    data.append((dom, tra, con, bri))
                except ValueError as ve:
                    print "line is: {}".format(line)
                    raise ve
            line_count += 1
    if (width is None or height is None or whiteval is None or
            range_size is None or domain_size is None or
            data == []):
        raise InvalidFileFormatError
    return (width, height, range_size, domain_size, whiteval, data)


def write_ifs(filename, width, height, whiteval, range_size, domain_size, ifs_data):
    """ write encoded ifs data to a file """
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
    parser.add_option('-v', '--verbose', action='store', type='int', default=0, help='verbosity level')
    parser.add_option('-z', '--zoom', action='store', type='int', default=1, help='fractal zoom level')
    options, _ = parser.parse_args()
    in_file = "input/" + options.file
    range_size = options.rangesize
    domain_size = options.domainsize
    ifs_file = "encoded_files/" + in_file.replace("input/", "").replace(".pgm", "") + "_r" + str(range_size) + "_d" + str(domain_size) + ".ifs"
    out_file = "output/" + ifs_file.replace("encoded_files/", "").replace(".ifs", ".pgm")
    verbosity = options.verbose

    start_time = datetime.datetime.now()
    print "started run at " + str(start_time)
    print "range size " + str(range_size)
    print "domain size " + str(domain_size)

    created_ifs = False

    if not os.path.exists(ifs_file):
        current_range = 0
        ifs_array = []
        if os.path.exists(ifs_file + ".part"):
            (width, height, range_size, domain_size, whiteval, ifs_array) = read_ifs(ifs_file + ".part")
            nranges = (width / range_size) * (height / range_size)
            current_range = len(ifs_array)
            print "ifs file part present - continuing from " + str(current_range) + "/" + str(nranges)
        else:
            print "ifs not present - creating ifs file from scratch"
        created_ifs = True
        print "opening image " + in_file
        (width, height, whiteval, data) = read_pgm(in_file)
        print "done"
        width = int(width)
        print "image width: " + str(width)
        height = int(height)
        print "image height: " + str(height)
        whiteval = int(whiteval)
        data = [int(val) for val in data]
        fit_threshold = 0  # float(range_size) * 0.001
        image = numpy_ifs.IFSImage(width, whiteval, range_size, domain_size, data)
        resized_domain_array = [None] * image.num_domains
        pgm_part_write = 1

        print "calculating best ifs transform for each range"
        calc_time = 0
        for irange in image.get_ranges(current_range):
            if current_range < 10:
                start = time()
            best_domain = None
            best_transform = None
            best_contrast = None
            best_brightness = None
            best_fit = 9999999999
            domain_num = 0
            for domain in image.get_domains():
                if resized_domain_array[domain_num] is None:
                    resized_domain_array[domain_num] = domain.resize(range_size)
                (transform, contrast, brightness, fit) = numpy_ifs.find_best_transform(irange, resized_domain_array[domain_num])
                if fit < best_fit:
                    best_fit = fit
                    best_domain = domain_num
                    best_transform = transform
                    best_contrast = contrast
                    best_brightness = brightness
                if fit <= fit_threshold:
                    break
                if verbosity > 1:
                    if domain_num % (image.num_domains / 100) == 0:
                        print("  done domain " + str(domain_num) +
                              " / " + str(image.num_domains) +
                              " (" + str((100 * domain_num) / image.num_domains) +
                              "% of range " + str(current_range + 1) +
                              " of " + str(image.num_ranges) + ")")
                domain_num += 1
            if verbosity > 0:
                if current_range % 1000 == 0:
                    print "done range " + str(current_range) + " (" + str(current_range + 1) + " of " + str(image.num_ranges) + ")"
            ifs_array.append((best_domain, best_transform, best_contrast, best_brightness))
            if current_range < 10:
                elapsed = time() - start
                calc_time += elapsed
            current_range += 1
            if current_range == 10:
                print "first 10 calculations took {} seconds".format(calc_time)
                if 1 / calc_time > 500:
                    pgm_part_write = 10000
                elif 1 / calc_time > 100:
                    pgm_part_write = 3000
                elif 1 / calc_time > 10:
                    pgm_part_write = 300
                elif 1 / calc_time > 1:
                    pgm_part_write = 30
                elif 1 / calc_time > 0.2:
                    pgm_part_write = 12
            if current_range % pgm_part_write == 0:
                write_ifs(ifs_file + ".part", width, height, whiteval, range_size, domain_size, ifs_array)

        print "finished calculations"

        write_ifs(ifs_file, width, height, whiteval, range_size, domain_size, ifs_array)
        os.remove(ifs_file + ".part")
    else:
        print "ifs present, opening ifs file"
        (width, height, range_size, domain_size, whiteval, ifs_array) = read_ifs(ifs_file)

    if options.zoom != 1:
        width = options.zoom * width
        height = options.zoom * height
        range_size = options.zoom * range_size
        domain_size = options.zoom * domain_size
        zoomed_ifs_array = []
        for an_ifs in ifs_array:
            zoomed_ifs_array.append((an_ifs[0] * options.zoom, an_ifs[1], an_ifs[2], an_ifs[3]))
        ifs_array = zoomed_ifs_array
        out_file = out_file.replace(".pgm", "_z" + str(options.zoom) + ".pgm")

    ifs_read_to_memory_time = datetime.datetime.now()
    print "ifs operations read into memory at " + str(ifs_read_to_memory_time)

    seed_data = [128] * width * height
    working_image = numpy_ifs.IFSImage(width, whiteval, range_size, domain_size, seed_data)

    order_of_convergence_iterations = 16 * (width / range_size) * (width / range_size)
    if options.iterations is None:
        num_ifs_to_apply = order_of_convergence_iterations * 4
    else:
        num_ifs_to_apply = options.iterations

    if options.print_intervals != 0:
        temp_file_dir = out_file.replace(".pgm", "")
        if not os.path.isdir(temp_file_dir):
            os.mkdir(temp_file_dir)

    test_sample_interval = working_image.num_ranges / 4
    force_range_scan_interval = working_image.num_ranges
    print "testing for convergence every " + str(test_sample_interval) + " ifs applied"
    print "forcing full range scan every " + str(force_range_scan_interval) + " ifs applied"
    test_image_data = working_image.data.copy()
    actual_ifs_applied_count = 0
    num_full_range_scan = 0
    for i in range(num_ifs_to_apply):
        range_num = random.randrange(len(ifs_array))
        if options.print_intervals != 0 and actual_ifs_applied_count % options.print_intervals == 0:
            temp_out_file = temp_file_dir + "/" + out_file.replace("output/", "").replace(".pgm", "") + "_i" + str(actual_ifs_applied_count) + ".pgm"
            working_image.write_pgm(temp_out_file)
        actual_ifs_applied_count += 1
        working_image.apply_ifs(range_num, ifs_array[range_num])
        if i != 0 and i % force_range_scan_interval == 0:
            # do full range scan
            num_full_range_scan += 1
            for (rnum, an_ifs) in enumerate(ifs_array):
                working_image.apply_ifs(rnum, an_ifs)
                actual_ifs_applied_count += 1
                if rnum != 0 and options.print_intervals != 0:
                    if actual_ifs_applied_count % options.print_intervals == 0:
                        temp_out_file = (temp_file_dir + "/" + out_file.replace("output/", "").replace(".pgm", "") +
                                         "_i" + str(actual_ifs_applied_count) + "_f" +
                                         str(num_full_range_scan) + ".pgm")
                        working_image.write_pgm(temp_out_file)
        if (actual_ifs_applied_count + 1) % test_sample_interval == 0:
            match = True
            for j in range(working_image.data.size):
                if working_image.data.item(j) != test_image_data.item(j):
                    match = False
                    break
            if match:
                print "IFS appears to have converged, doing one full range scan"
                for (rnum, an_ifs) in enumerate(ifs_array):
                    working_image.apply_ifs(rnum, an_ifs)
                    actual_ifs_applied_count += 1
                for k in range(len(working_image.data)):
                    if working_image.data.item(k) != test_image_data.item(k):
                        print "   it hadn't converged"
                        test_image_data = working_image.data.copy()
                        match = False
                        break
                if match:
                    print "Exiting loop as ifs has converged"
                    temp_out_file = temp_file_dir + "/" + out_file.replace("output/", "").replace(".pgm", "") + "_i" + str(actual_ifs_applied_count) + ".pgm"
                    working_image.write_pgm(temp_out_file)
                    break
            else:
                test_image_data = working_image.data.copy()

    finished_operations_time = datetime.datetime.now()

    working_image.write_pgm(out_file)

    print "completed reconstructing image at " + str(finished_operations_time)

    step_one_duration = ifs_read_to_memory_time - start_time
    step_two_duration = finished_operations_time - ifs_read_to_memory_time

    if created_ifs:
        print "created ifs file in " + str(step_one_duration)
    else:
        print "loaded ifs file in " + str(step_one_duration)
    print "reconstructed image in " + str(step_two_duration)

main()
