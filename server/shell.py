import json
import requests
import sys

from argparse import ArgumentParser

def get_num_connections(server):
    """
    Hit the server and get the number of open sockets.
    @param str: server, The address of the server to hit.
    @return int, The number of open connections
    """
    response = requests.get('http://{addr}/stats/'.format(addr=server))
    return response.json.get('connections', 0)

def run_command(server, command):
    """
    POST a command to the server to be run on all clients.
    @param str: server, The address of the server to hit.
    @param str: command, The command to run.
    """
    cmd = {
        'cmd': command,
    }

    headers = {
        'Content-Type': 'application/json',
    }

    r = requests.post('http://{addr}/cmd/'.format(addr=server), data=json.dumps(cmd), headers=headers)
    print r

def parse_args():
    """
    Parse and return arguments from the command line
    """
    parser = ArgumentParser(description='Run commands through a polysocket server')
    parser.add_argument('--server', dest='server', metavar='s', type=str, default='127.0.0.1', help='The address of the server to connect to')
    parser.add_argument('--port', dest='port', metavar='p', type=str, default='8888', help='The port that the server is running on')
    return parser.parse_args()

def main():
    """
    The main loop of the shell.
    """
    args = parse_args()
    server = '{server}:{port}'.format(server=args.server, port=args.port)
    print 'Polysocket shell v0.1'
    print 'Connected to server at {server}'.format(server=server)
    while True:
        conns = get_num_connections(server)
        sys.stdout.write('polysocket ({conns})> '.format(conns=conns))
        cmd = raw_input()
        if cmd:
            print '>>> {writeback}'.format(writeback=cmd)
            run_command(server, cmd)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print ''
    except EOFError:
        print ''
