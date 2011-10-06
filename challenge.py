#!/usr/bin/python

import struct
from pyDes import *
from binascii import hexlify, unhexlify 

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
longlongint1=struct.unpack('>Q',struct.pack('8s', D1))[0]
longlongint2=struct.unpack('>Q',struct.pack('8s', nt2))[0]
buff=struct.unpack('8s',struct.pack('>Q', longlongint1 ^ longlongint2))[0]

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

