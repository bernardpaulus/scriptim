#!/usr/bin/python

import sys
from binascii import hexlify, unhexlify 
import random
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

def int2binstr(i):
    """converts an arbitrary-sized int to a binary string"""
    c = hex(i)[2:]
    if c[-1] in 'L' or 'l':
        c=c[:-1]
    return unhexlify(c)

def decipher_key(data, crypt_algo, key=None):
    """ first step of authentification computation : decipher the given data (a
nonce) with the authentification key

    - data must be a 8 bytes long binary string. If not, zero padding will be
      performed in front
    - crypt_algo must be a "des" or "3des", 
    - key length must be 8 and (16 or 24) bytes long, for respecively des and
      triple des.
    """
    if key is None:
        key = unhexlify("00"*8)

    if len(key) not in [8, 16, 24]:
        raise ValueError("invalid key size: not in [8, 16, 24]")

    IV=unhexlify("00"*8)
    if crypt_algo not in ["des", "3des"]:
        raise NotImplementedError("crypt_algo not supported: "+str(crypt_algo))
    elif crypt_algo == "des":
        crypt_box=des(key, CBC, pad=None, padmode=PAD_NORMAL)
    elif crypt_algo == "3des":
        crypt_box=des(key, CBC, pad=None, padmode=PAD_NORMAL)
    crypt_box.setIV(IV)
    return crypt_box.decrypt(data)

def generate_challenge_response(encrypted_nonce, cryp_algo="des", key=None,\
        verbose=False, replay_example=False):
    """generate the response to a nonce

    - nonce must be a 8 bytes long binary string. 
    - crypt_algo must be a "des" or "3des", 
    - key length must be 8 and (16 or 24) bytes long, for respecively des and
      triple des.
    - verbose triggers message printing
    - replay_example set to true takes 0x1122334455667788 as nonce

    returns the circular shift << by one byte of our own nonce, and the
    response, the decrypted version of the nonce of the card and our own nonce.
    """
    # a
    nt=decipher_key(data, cryp_algo)
    nt2 = nt[1:]+nt[:1] # 8-byte string
    
    # b
    nr = replay_example and int2binstr(0x1122334455667788) \
            or int2binstr(random.getrandbits(8*8))
    nr2 = nr[1:]+nr[:1] # for verification purposes
    D1=decipher_key(nr, cryp_algo)
    
    # c : perform cbc decrypt manually
    c = hex(int(hexlify(D1), 16) ^ int(hexlify(nt2), 16))[2:][:-1]
    if len(c) < 16: # complete if too short
        c = "0"*(16-len(c)) + c
    
    buff=unhexlify(c)
    
    # d
    D2=decipher_key(buff, cryp_algo)
    
    # e
    # Doxo...ooo(nr||nt2) = D1||D2
    concat=D1+D2
    if verbose:
        print "nt = ", hexlify(nt)
        print "nt2 = ", hexlify(nt2)
        print "D1 = ", hexlify(D1)
        print "D2 = ", hexlify(D2)
        print "D1||D2 = ", hexlify(concat)
    return [nr2, concat]


if __name__ == "__main__":
    print "Insert Encrypted Nonce (or <enter for the example)"
    data=unhexlify(data_input() or "6E7577944ADFFC0C")
    replay = False
    if data == unhexlify("6E7577944ADFFC0C"):
        replay = True
    
    nr2, d1d2 = generate_challenge_response(data, "des", key=None, verbose=True,
            replay_example = replay)
    
    print "INSERT DESFire RESPONSE: (or <enter for the example)"
    resp=unhexlify(data_input() or "AD6CC16025CCFB7B")
    
    d_resp=decipher_key(resp, "des")
    if d_resp == nr2:
        print "OK: matches circular shift of nr"
        print "nr2 = ", hexlify(nr2)
    else:
        print "KO !!!"
        print "d_resp = ", hexlify(d_resp)
        print "nr2 = ", hexlify(nr2)
    
