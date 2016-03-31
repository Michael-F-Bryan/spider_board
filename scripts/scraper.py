import argparse
import os
import sys
import spider_board


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Your username')
    parser.add_argument('password', help='Your password')
    parser.add_argument('-s', '--sequential', dest='sequential', 
            action='store_true', help='Run sequentially')
    parser.add_argument('-t', '--threads', dest='threads', type=int, default=20,
            help='Number of threads to use (default: 20)')
    parser.add_argument('-d', '--destination', dest='destination',
            help='Where to output the downloaded files')
    parser.add_argument('-m', '--max-size', dest='max_size',
            help='The maximum download size in megabytes (default: 10MB)')
    parser.add_argument('-f', '--force', dest='force', action='store_true',
            help='Overwrite files if they already exist (default: False)')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
            help='Enable verbose output')

    args = parser.parse_args(argv)

    username = args.username
    password = args.password

    if args.sequential:
        run_sequentially = True
    else:
        run_sequentially = False

    if args.destination:
        download_dir = os.path.expanduser(args.destination)
    else:
        download_dir = os.path.expanduser('~/Downloads/Blackboard/')

    if args.verbose:
        import logging
        spider_board.logger.setLevel(logging.DEBUG)

    print('Downloading files to {}'.format(os.path.abspath(download_dir)))

    bob = spider_board.Browser(
            username, 
            password, 
            download_dir,
            seq=run_sequentially,
            max_size=args.max_size or 10*1024*1024,
            force=args.force)

    bob.start()


if __name__ == "__main__":
    main(sys.argv[1:])
