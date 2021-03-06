
import time
from instantauth import Authentication, SessionHandler
from instantauth.cryptors import PlainCryptor
from instantauth.cryptors.aes import AESCryptor
from instantauth.verifiers import BypassVerifier, DataKeyVerifier
from instantauth.verifiers.timehash import TimeHashVerifier
from instantauth.coders import PlainCoder
from instantauth.coders.base64 import Base64Coder
from instantauth.coders.urlquery import URLQueryCoder, SimpleURLQueryCoder
from instantauth.coders.json import JsonCoder
from instantauth.flask import FlaskAuthentication

session_zero = {'id': 0}

class TestSessionHandler(SessionHandler):
    def session_from_public_key(self, public_key):
        return {'id': public_key}

    def get_public_key(self, session):
        return 'public_key'

    def get_private_key(self, session):
        return 'private_key'

def test_plain_bypass_urlquery():
    auth = Authentication(PlainCoder(), PlainCryptor(), BypassVerifier(), URLQueryCoder(), TestSessionHandler(), 'SECRET')

    data = ''
    context = auth.get_context(data)
    assert context.data == {}

    data = 'field=value'
    context = auth.get_context(data)
    assert context.data == {'field': ['value']}

    data = 'field=value&field=value'
    context = auth.get_context(data)
    assert context.data == {'field': ['value', 'value']}

def test_plain_bypass_simpleurlquery():
    auth = Authentication(PlainCoder(), PlainCryptor(), BypassVerifier(), SimpleURLQueryCoder(), TestSessionHandler(), 'SECRET')

    data = 'field=value'
    context = auth.get_context(data)
    assert context.data == {'field': 'value'}

def test_plain_datakey_json():
    auth = Authentication(PlainCoder(), PlainCryptor(), DataKeyVerifier(JsonCoder(), 'session'), PlainCoder(), TestSessionHandler(), 'SECRET')

    data = '{"field": "value", "session": "1"}'
    context = auth.get_context(data)
    assert context.data == {'field': 'value', 'session': '1'}
    assert context.session == {'id': '1'}

def test_session():
    private_key = ('private_key' + '!' * 40)[:40]
    public_key = ('public_key' + '!' * 40)[:40]
    class KeyCheckSessionHandler(SessionHandler):
        def session_from_public_key(a_public_key, secret_key):
            assert a_public_key == public_key
            return session

        def get_private_key(session, secret_key):
            return private_key

    verifier = TimeHashVerifier()
    auth = Authentication(PlainCoder(), PlainCryptor(), verifier, SimpleURLQueryCoder(), TestSessionHandler(), 'SECRET')

    data = {'field': 'value'}
    encrypted = auth.build_data(data, session_zero)
    assert encrypted.startswith('public_key')
    assert '$' in encrypted

    context = auth.get_context(encrypted)
    assert context.data == data

def test_flask():
    data = {'field': 'value'}
    verifier = TimeHashVerifier()
    auth = FlaskAuthentication(Base64Coder(), AESCryptor(128), verifier, SimpleURLQueryCoder(), TestSessionHandler(), 'SECRET')
    encrypted = auth.build_data(data, session_zero)

    context = auth.get_context(encrypted)
    assert context.data == data

