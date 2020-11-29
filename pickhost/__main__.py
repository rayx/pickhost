import argparse
import sys
from pickhost import PickHost
from pickhost import __version__ as version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='file', metavar='file',
                        help='config file')
    parser.add_argument('-e', dest='edit', action='store_true',
                        help='edit config file rather than show it')
    parser.add_argument('-v', dest='version', action='store_true',
                        help='print version')
    args = parser.parse_args()
    if args.version:
        print("Pickhost %s" % version)
        sys.exit(0)
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
            sys.stderr.write('export %s="%s"\n' % ('PH_' + key.upper(), value))


if __name__ == '__main__':
    main()
