import argparse
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

    args = parser.parse_args(argv)

    username = args.username
    password = args.password

    if args.sequential:
        run_sequentially = True
    else:
        run_sequentially = False

    username = '17052933'
    password = 'Popcorn37'

    bob = spider_board.Browser(username, password, seq=run_sequentially)
    bob.start()

    print(bob.documents.qsize())


if __name__ == "__main__":
    main(sys.argv[1:])
