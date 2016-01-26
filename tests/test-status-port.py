#!/usr/local/bin/python

# Creates a ghostunnel. Ensures that /_status endpoint works.

from subprocess import Popen
from test_common import create_root_cert, create_signed_cert, LOCALHOST, SocketPair, print_ok, cleanup_certs
import urllib2, socket, ssl, time, os, signal, json

if __name__ == "__main__":
  ghostunnel = None
  try:
    # Step 1: create certs
    create_root_cert('root')
    create_signed_cert('server', 'root')
    create_signed_cert('new_server', 'root')
    create_signed_cert('client1', 'root')

    # Step 2: start ghostunnel
    ghostunnel = Popen(['../ghostunnel', '--listen={0}:13001'.format(LOCALHOST),
      '--target={0}:13100'.format(LOCALHOST), '--keystore=server.p12',
      '--storepass=', '--cacert=root.crt', '--allow-ou=client1',
      '--status=localhost:13100'])

    # Step 3: read status information
    time.sleep(5)
    status = json.loads(urllib2.urlopen("https://localhost:13100/_status", cafile='root.crt').read())
    metrics = json.loads(urllib2.urlopen("https://localhost:13100/_metrics", cafile='root.crt').read())

    if not status['ok']:
        raise Exception("ghostunnel reported non-ok status")

    if type(metrics) != list:
        raise Exception("ghostunnel metrics expected to be JSON list")

    # Step 4: reload
    os.rename('new_server.p12', 'server.p12')
    ghostunnel.send_signal(signal.SIGUSR1)
    time.sleep(10)

    # Step 3: read status information
    # expecting tunnel to use "new_server" cert, setting cafile accordingly
    status = json.loads(urllib2.urlopen("https://localhost:13100/_status", cafile='root.crt').read())
    metrics = json.loads(urllib2.urlopen("https://localhost:13100/_metrics", cafile='root.crt').read())

    if not status['ok']:
        raise Exception("ghostunnel reported non-ok status")

    if type(metrics) != list:
        raise Exception("ghostunnel metrics expected to be JSON list")

    print_ok("OK")
  finally:
    if ghostunnel:
      ghostunnel.kill()
    cleanup_certs(['root', 'server', 'new_server', 'client1'])
