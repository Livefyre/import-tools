from validator import validate
import sys

def validate_archive(infile, outfile='validator_results.txt'):
	validate(infile, outfile, is_archive=True)

def main():
    args = sys.argv[1:]
    if len(args) not in (1,2,3):
        print 'Usage: python archive_validator.py [input file] [~optional schema file] [~optional output file]'
        sys.exit(0)
    validate_archive(*args)

if __name__ == '__main__':
    main()