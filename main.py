from Parser import Parser


def main():
    parser = Parser("tokens.txt")
    parser.parse()
    parser.print()


if __name__ == "__main__":
    main()