#!/usr/local/bin/python

import socket, os, sys, logging
from optparse import OptionParser

usage = 'usage: %prog [options] arg1 arg2'
parser = OptionParser(usage="%prog [-r] [-q] [-h]", version="%prog 1.0")
parser.add_option("-v", "--verbose",
     action="store_true", dest="verbose", default=False,
     help="make lots of noise [default]")
parser.add_option("-q", "--quiet",
     action="store_false", dest="verbose", default=True,
     help="be vewwy quiet (I'm hunting wabbits)")
parser.add_option("-r", "--restart",
     action="store_true", dest="restart", default=False,
     help="Should I actually restart gmetad")
(options, args) = parser.parse_args()

LOG_FILENAME = '/var/logs/gmetad.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.NOTSET)

def restartGmetad():
    cmd = 'service gmetad restart'
    pipe = os.popen(cmd)
    results = [l for l in pipe.readlines() if l.find('OK') != -1]
    if results:
        return True
    else:
        return False

def gmetadXmlChecker(port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", port))
        data = client_socket.recv(512)
        if  len(data) < 512:
            logging.critical('We didn\'t recieve any output from gmetad running on port: %d' % port)
            if options.verbose:
                print "We didn\'t recieve any output from gmetad running in port: %d" % port
            client_socket.close()
	    return False
        else:
            #print "RECIEVED:" , data
            client_socket.close()
	    return True
    except Exception as e:
        logging.critical('Gmetad does not seem to be running on this port')
        if options.verbose:
            print "Cannot connect to host"
 	return False


def main():
    try:
        gmetad_confs = os.listdir('/etc/gmetad')
    except:
        logging.critical('Directory does not exist')
        if options.verbose:
            print 'Directory does not exist'
        exit()
    xml_ports = []
    for conf in gmetad_confs:
        for line in open('/etc/gmetad/' + conf):
            if 'xml_port' in line:
                xml_ports.append(int(line.split(' ')[1].rstrip('\n')))

    for port in xml_ports:
        if gmetadXmlChecker(port) == True:
            logging.info('gmetad on port: %d is running correctly, exiting' % port)
            if options.verbose:
                print "gmetad on port: %d is running correctly, exiting" % port
        else:
            logging.critical('gmetad on port: %d  is not responding, restarting' % port)
            if options.verbose:
                print "gmetad on port: %d  is not responding, restarting" % port
            if options.restart:
                restartGmetad()
                exit()

if __name__ == '__main__':
    main()
