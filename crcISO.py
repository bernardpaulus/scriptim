
""" crcISO.py Clone of crcISO.c. Code snippet by adam laurie """
from binascii import hexlify, unhexlify 


def crc16_iso14443a(data):
    """takes a data string and returns [crclow, crchigh] bytes"""
    crc= 0x6363
    return crc16_iso14443ab(data, crc, 0x8408, False)

def crc16_iso14443b(data):
    crc= 0xffff
    return crc16_iso14443ab(data, crc, 0x8408, True)

def crc16_iso14443ab(data, crc, polynomial, invert):
    for byte in [int(hexlify(c), 16) for c in data]:
        crc= crc ^ byte
        for bit in range(8):
            if crc & 0x0001:
                crc= (crc >> 1) ^ polynomial
            else:
                crc= crc >> 1
    crclow= crc & 0xff
    crchigh= (crc >> 8) & 0xff
    if invert:
        crclow= 256 + ~crclow
        crchigh= 256 + ~crchigh
    return [crclow, crchigh]

if __name__ == "__main__":
    from challenge import data_input
    # You put in BuffCRC_A the 16-byte data that you want to compute
    print "Insert the data to process for the CRC-16 (or <enter> for default)"
    data=unhexlify(data_input() or "11223344556677889900aabbccddeeff")
     
    print("CRC_A of ") 
    print(hexlify(data)) 
    
    print(" iso14443a: ") 
    print ([hex(c) for c in crc16_iso14443a(data)])
    #print(" iso14443b: ") 
    #print ([hex(c) for c in crc16_iso14443b(data)])
    print("expected default : 0xd75a")
