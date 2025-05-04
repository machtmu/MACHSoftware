def condense_file(input_filename, output_filename):
    with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
        for i, line in enumerate(infile):
            if i % 1000 == 0:  # Keep only one line from every 100
                outfile.write(line)

if __name__ == '__main__':
    input_file = r"C:\Users\Mach_\OneDrive\Documents\MACH_OS_v6\v2 mach\Dat_.csv"
    output_file = r"C:\Users\Mach_\OneDrive\Documents\MACH_OS_v6\v2 mach\condensed_datav5.csv"
    condense_file(input_file, output_file)
