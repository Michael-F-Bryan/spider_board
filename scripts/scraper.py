import spider_board


def main():
    username = '17052933'
    password = 'Popcorn37'

    bob = spider_board.Browser(username, password)
    bob.login()
    bob.get_units()


if __name__ == "__main__":
    main()
