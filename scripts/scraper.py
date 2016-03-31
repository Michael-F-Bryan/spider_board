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
    parser.add_argument('-t', '--threads', dest='threads', type=int, default=8,
            help='Number of threads to use (default: 8)')
    parser.add_argument('-d', '--destination', dest='destination',
            help='Where to output the downloaded files')
    parser.add_argument('-m', '--max-size', dest='max_size',
            help='The maximum download size in bytes (default: 10MB)')

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


    print('Downloading files to {}'.format(os.path.abspath(download_dir)))

    bob = spider_board.Browser(
            username, 
            password, 
            download_dir,
            seq=run_sequentially,
            max_size=args.max_size or 10*1024)

    bob.start()
    
    bob.download_files()


if __name__ == "__main__":
    main(sys.argv[1:])
