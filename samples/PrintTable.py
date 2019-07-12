import fxcmrest
import argparse

tables = ['Offer', 'OpenPosition', 'ClosedPosition', 'Order', 'Summary', 'Account', 'Properties']

parser = argparse.ArgumentParser()
parser.add_argument('token', help="token to use when logging in")
parser.add_argument('--server', '-s', default="demo", help="server to connect to (demo/real)")
parser.add_argument('--table', '-t', default="Account", help="table to print", choices=tables, nargs='*')
args = parser.parse_args()

c = fxcmrest.Config(file="{0}.json".format(args.server), token=args.token, agent="fxcmrest-login.py-example")
r = fxcmrest.FXCMRest(c)
r.connect()

resp = r.request('GET','/trading/get_model', {'models':args.table}).json()
print(resp)
input("Press enter key to exit")