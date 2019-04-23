import argparse
import sys
from pickhost import PickHost


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='file', metavar='file',
                        help='config file')
    parser.add_argument('-e', dest='edit', action='store_true',
                        help='edit config file rather than show it')
    args = parser.parse_args()
    p = PickHost(args.file)
    if args.edit:
        p.edit()
        sys.exit(0)
    # If config file is empty there is no point to show it.
    if not p.config.groups:
        sys.exit("File %s is empty. Please rerun the command with "
                 "-e option to add hosts first." % p.config.file)
    result = p.run()
    # If user selected an entry, print it to stderr, in a form that can
    # be consumed by shell script.
    if result:
        for key, value in result.items():
            sys.stderr.write('export %s=%s\n' % ('PH_' + key.upper(), value))


if __name__ == '__main__':
    main()
