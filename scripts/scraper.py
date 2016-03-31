import spider_board


def main():
    username = '17052933'
    password = 'Popcorn37'

    bob = spider_board.Browser(username, password, threads=1)
    bob.start()

    # bob.login()
    # bob.get_units()

    # a_unit = bob.units[0]
    # bob.find_documents(a_unit)

    # print(a_unit.documents.qsize())


if __name__ == "__main__":
    main()
