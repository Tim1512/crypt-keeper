from uuid import uuid4
from Crypto import Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from secret_store.helper import encode_key, decode_key
from re import match
from boto3 import client
from botocore.client import Config
from crypt_keeper_server.configuration import CONFIGURATION

PUT = 'PUT'
GET = 'GET'
SEED_LENGTH = CONFIGURATION.lookup('symmetric_key:seed_length', 128)
SYMMETRIC_KEY_LENGTH = CONFIGURATION.lookup('symmetric_key:length', 32)
S3_URL_EXPIRATION_TIMEOUT = CONFIGURATION.lookup('s3:url_expiration_timeout', 600)
S3_BUCKET = CONFIGURATION.lookup('s3:bucket')

client_method_map = {
    GET: 'get_object',
    PUT: 'put_object',
}


def decrypt(encrypted_symmetric_key, private_key):
    decoded_encrypted_symmetric_key = decode_key(encrypted_symmetric_key)
    decoded_private_key = private_key
    if not match(r'-+BEGIN RSA PRIVATE KEY-+', private_key):
        decoded_private_key = decode_key(private_key)
    key = RSA.importKey(decoded_private_key)
    cipher = PKCS1_OAEP.new(key)
    symmetric_key = cipher.decrypt(decoded_encrypted_symmetric_key)
    return encode_key(symmetric_key)


def encrypt(symmetric_key, public_key):
    decoded_symmetric_key = decode_key(symmetric_key)
    decoded_public_key = public_key
    if not match(r'-+BEGIN PUBLIC KEY-+', public_key):
        decoded_public_key = decode_key(public_key)
    key = RSA.importKey(decoded_public_key)
    cipher = PKCS1_OAEP.new(key)
    encrypted_symmetric_key = cipher.encrypt(decoded_symmetric_key)
    return encode_key(encrypted_symmetric_key)


def sign_url(document_id, method=GET):
    client_method = client_method_map.get(method, GET)
    s3 = client('s3', config=Config(signature_version='s3v4'))
    params = {
        'Key': '%s' % document_id,
        'Bucket': S3_BUCKET,
    }
    url = s3.generate_presigned_url(ClientMethod=client_method,
                                    Params=params,
                                    ExpiresIn=S3_URL_EXPIRATION_TIMEOUT)
    return url


def check_bucket_exists(bucket_name):
    return False


def create_bucket(bocket_name):
    pass


def generate_symmetric_key(key_size=SYMMETRIC_KEY_LENGTH):
    seed = '1337:Crypt-Keeper:'.encode('utf-8') + Random.new().read(SEED_LENGTH)
    symmetric_key = SHA256.new(seed).digest()[:key_size]
    return encode_key(symmetric_key)


def generate_document_id(document_metadata):
    return uuid4()
