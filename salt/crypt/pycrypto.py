# -*- coding: utf-8 -*-
'''
Module for pycrypto cryptography routines
'''
# Import Python libraries
import os
import logging
import hashlib

# Import salt libraries
import salt.utils

# Import pycrypto libraries
try:
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Hash import SHA
    from Crypto.PublicKey import RSA
    from Crypto.Signature import PKCS1_v1_5
    # let this be imported, if possible
    import Crypto.Random  # pylint: disable=W0611
except ImportError:
    # No need for crypt in local mode
    pass

log = logging.getLogger(__name__)

class Crypt(object):  # TODO Start to build out mixins
    '''
    Pycrypto routines
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
        base = os.path.join(keydir, keyname)
        priv = '{0}.pem'.format(base)
        pub = '{0}.pub'.format(base)

        salt.utils.reinit_crypto()  # TODO Make sure this handles all back-ends
        gen = RSA.generate(bits=keysize, e=65537)
        if os.path.isfile(priv):
            # Between first checking and the generation another process has made
            # a key! Use the winner's key
            return priv
        cumask = os.umask(191)
        with salt.utils.fopen(priv, 'wb+') as f:
            f.write(gen.exportKey('PEM'))
        os.umask(cumask)
        with salt.utils.fopen(pub, 'wb+') as f:
            f.write(gen.publickey().exportKey('PEM'))
        os.chmod(priv, 256)
        if user:
            try:
                import pwd

                uid = pwd.getpwnam(user).pw_uid
                os.chown(priv, uid, -1)
                os.chown(pub, uid, -1)
            except (KeyError, ImportError, OSError):
                # The specified user was not found, allow the backup systems to
                # report the error
                pass
        return priv

    @staticmethod
    def sign_message(privkey_path, message):
        '''
        Use Crypto.Signature.PKCS1_v1_5 to sign a message. Returns the signature.
        '''
        log.debug('salt.crypt.sign_message: Loading private key')
        with salt.utils.fopen(privkey_path) as f:
            key = RSA.importKey(f.read())
        log.debug('salt.crypt.sign_message: Signing message.')
        signer = PKCS1_v1_5.new(key)
        return signer.sign(SHA.new(message))

    @staticmethod
    def verify_signature(pubkey_path, message, signature):
        '''
        Use Crypto.Signature.PKCS1_v1_5 to verify the signature on a message.
        Returns True for valid signature.
        '''
        log.debug('salt.crypt.verify_signature: Loading public key')
        with salt.utils.fopen(pubkey_path) as f:
            pubkey = RSA.importKey(f.read())
        log.debug('salt.crypt.verify_signature: Verifying signature')
        verifier = PKCS1_v1_5.new(pubkey)
        return verifier.verify(SHA.new(message), signature)

    @staticmethod
    def private_encrypt(key, message):
        '''
        Generate an M2Crypto-compatible signature

        :param Crypto.PublicKey.RSA._RSAobj key: The RSA key object
        :param str message: The message to sign
        :rtype: str
        :return: The signature, or an empty string if the signature operation failed
        '''
        signer = salt.utils.rsax931.RSAX931Signer(key.exportKey('PEM'))
        return signer.sign(message)

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
        verifier = salt.utils.rsax931.RSAX931Verifier(pub.exportKey('PEM'))
        return verifier.verify(message)

    # Begin instance methods

    def import_key(self, path):
        '''
        Import an RSA key and return it, selecting the proper path by inspecting opts
        :return: RSA key
        '''
        if os.path.exists(path):
            with salt.utils.fopen(path) as f:
                key = RSA.importKey(f.read())
            log.debug('Loaded key in path: {0}'.format(path))
            return key

    def decrypt_aes_with_key(self, payload, key, mpub, master_pub=True):
        cipher = PKCS1_OAEP.new(key)
        key_str = cipher.decrypt(payload['aes'])
        if 'sig' in payload:
            m_path = os.path.join(self.opts['pki_dir'], mpub)
            if os.path.exists(m_path):
                try:
                    mkey = self.import_key(m_path)
                except Exception:
                    return '', ''
                digest = hashlib.sha256(key_str).hexdigest()
                m_digest = self.public_decrypt(mkey.publickey(), payload['sig'])
                if m_digest != digest:
                    return '', ''
        else:
            return '', ''
        if '_|-' in key_str:
            return key_str.split('_|-')
        else:
            if 'token' in payload:
                token = cipher.decrypt(payload['token'])
                return key_str, token
            elif not master_pub:
                return key_str, ''
        return '', ''