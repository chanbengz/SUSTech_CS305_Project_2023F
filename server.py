from argparse import ArgumentParser
from threading import Thread

parser = ArgumentParser()
parser.add_argument('--ip', '-i', type=str)
parser.add_argument('--port', '-p', type=int)
args = parser.parse_args()
PORT = args.port or 8080

if __name__ == "__main__":
