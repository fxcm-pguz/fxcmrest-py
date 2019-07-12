import fxcmrest
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('token', help="token to use when logging in")
parser.add_argument('--server', '-s', default="demo", help="server to connect to (demo/real)")
args = parser.parse_args()

c = fxcmrest.Config(file="{0}.json".format(args.server), token=args.token, agent="fxcmrest-login.py-example")
r = fxcmrest.FXCMRest(c)
print(r.connect())
input("Press enter key to exit")