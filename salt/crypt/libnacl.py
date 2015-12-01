# -*- coding: utf-8 -*-
#
# Import libnacl libraries
try:
    import libnacl
except ImportError:
    # No need for crypt in local mode
    pass

class Crypt(object):  # TODO Start to build out mixins
    '''
    libnacl routines
    '''
    def __init__(self, opts):
        self.opts = opts

    @staticmethod
    def gen_keys(keydir, keyname, keysize, user=None):
        '''
        Generate a RSA public keypair for use with salt
        :param str keydir: The directory to write the keypair to
        :param str keyname: The type of salt server for whom this key should be written. (i.e. 'master' or 'minion')
        :param int keysize: The number of bits in the key
        :param str user: The user on the system who should own this keypair
        :rtype: str
        :return: Path on the filesystem to the RSA private key
        '''
        raise NotImplementedError

    @staticmethod
    def sign_message(privkey_path, message):
        '''
        Sign a message. Return the signature.
        :param privkey_path:
        :param message: The message to be returned
        :return: The signature
        '''
        raise NotImplementedError

    @staticmethod
    def verify_signature(pubkey_path, message, signature):
        raise NotImplementedError

    @staticmethod
    def private_encrypt(key, message):
        # TODO Correct documentation
        '''
        Generate an M2Crypto-compatible signature

        :param Crypto.PublicKey.RSA._RSAobj key: The RSA key object
        :param str message: The message to sign
        :rtype: str
        :return: The signature, or an empty string if the signature operation failed
        '''
        raise NotImplementedError

    @staticmethod
    def public_decrypt(pub, message):
        '''
        Verify an M2Crypto-compatible signature

        :param Crypto.PublicKey.RSA._RSAobj key: The RSA public key object
        :param str message: The signed message to verify
        :rtype: str
        :return: The message (or digest) recovered from the signature, or an
            empty string if the verification failed
        '''
        raise NotImplementedError