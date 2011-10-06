#!/usr/bin/python

import sys
from binascii import hexlify, unhexlify 
try:
    from pyDes import *
except ImportError:
    print """Module pyDes not available
    to install it:
        download it from http://sourceforge.net/projects/pydes/
        unzip it
        run : sudo python pyDes-2.0.1/setup.py install
    You're done!
"""
    sys.exit(1)

def data_input():
    return ''.join([x for x in raw_input() if x in "0123456789ABCDEFabcdef"])

def decipher_master_key(data):
    master_key=unhexlify("00"*8)
    IV=unhexlify("00"*8)
    des_box=des(master_key, CBC, pad=None, padmode=PAD_NORMAL)
    des_box.setIV(IV)
    return des_box.decrypt(data)

print "Insert Encrypted Nonce (or <enter for the example)"
data=unhexlify(data_input() or "6E7577944ADFFC0C")

# a
nt=decipher_master_key(data)
print "nt = ", hexlify(nt)
nt2 = nt[1:]+nt[:1] # 8-byte string
print "nt2 = ", hexlify(nt2)

# b
nr=unhexlify("1122334455667788")
nr2 = nr[1:]+nr[:1] # for verification purposes
D1=decipher_master_key(nr)
print "D1 = ", hexlify(D1)

# c
buff=int(hexlify(D1), 16) ^ int(hexlify(nt2)

# d
D2=decipher_master_key(buff)
print "D2 = ", hexlify(D2)

# e
# Doxo...ooo(nr||nt2) = D1||D2
print "D1||D2 = ", hexlify(D1)+hexlify(D2)

print "INSERT DESFire RESPONSE: (or <enter for the example)"
resp=unhexlify(data_input() or "AD6CC16025CCFB7B")

d_resp=decipher_master_key(resp)
if d_resp == nr2:
    print "OK: matches circular shift of nr"
    print "nr2 = ", hexlify(nr2)
else:
    print "KO !!!"
    print "d_resp = ", hexlify(d_resp)
    print "nr2 = ", hexlify(nr2)

