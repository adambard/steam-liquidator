import argparse
import getpass

from liquidator import api

parser = argparse.ArgumentParser(description='Liquidate your Steam Inventory')
parser.add_argument('-u, --username', type=str, help='Your steam username', dest='username')


def main():
    args = parser.parse_args()
    username = args.username or input("Enter your Steam username: ")
    password = getpass.getpass("Enter your Steam password: ")

    api.liquidate(username, password)


if __name__ == '__main__':
    main()
