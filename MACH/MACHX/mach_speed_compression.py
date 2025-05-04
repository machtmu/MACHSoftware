def condense_file(input_filename, output_filename):
    with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
        for i, line in enumerate(infile):
            if i % 500 == 0: # Keep only one line from every 100
                outfile.write(line)

# Example usage
input_filename = r'C:\Users\Mach_\Documents\MACH_OS_v3\v2 mach\MACHHH\MACHX\boi.csv' # Input file containing the original data
output_filename = 'condensed_data.csv' # Output file to save the condensed data
condense_file(input_filename, output_filename)