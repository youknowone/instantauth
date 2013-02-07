
from .environment import nothing_environment
from prettyexc import PrettyException

class AuthenticationError(PrettyException):
    pass

class Authentication(object):
    def __init__(self, env, session_handler, secret_key):
        self.env = env
        self.session_handler = session_handler
        self.secret_key = secret_key

    def _merge_context(self, context):
        for k, v in self.env.cryptor.derived_context.items():
            setattr(context, k, v)
        for k, v in self.env.verifier.derived_context.items():
            setattr(context, k, v)
        for k, v in self.env.coder.derived_context.items():
            setattr(context, k, v)

    def get_first_context(self, data):
        decrypted = self.env.cryptor.decrypt_global(data, self.secret_key)
        verifier, encrypted_data = self.env.verifier.divide_verifier_data(decrypted, self.secret_key)
        public_key = self.env.verifier.public_key_from_verifier(verifier, self.secret_key)
        raw_data = self.env.cryptor.decrypt_data(encrypted_data, self.secret_key, self.secret_key)
        semantic_data = self.env.coder.decode(raw_data)
        context = Context(None, semantic_data)
        context.auth_key = public_key
        self._merge_context(context)
        return context

    def get_context(self, data):
        decrypted = self.env.cryptor.decrypt_global(data, self.secret_key)
        verifier, encrypted_data = self.env.verifier.divide_verifier_data(decrypted, self.secret_key)
        public_key = self.env.verifier.public_key_from_verifier(verifier, self.secret_key)
        if not public_key:
            raise AuthenticationError
        try:
            session = self.session_handler.session_from_public_key(public_key)
        except KeyError:
            raise AuthenticationError
        if not session:
            raise AuthenticationError
        private_key = self.session_handler.get_private_key(session)
        if not self.env.verifier.verify(verifier, private_key, self.secret_key):
            raise AuthenticationError
        raw_data = self.env.cryptor.decrypt_data(encrypted_data, self.secret_key, private_key)
        semantic_data = self.env.coder.decode(raw_data)
        context = Context(session, semantic_data)
        self._merge_context(context)
        return context

    def build_data(self, session, data):
        private_key = self.session_handler.get_private_key(session)
        public_key = self.session_handler.get_public_key(session)
        coded_data = self.env.coder.encode(data)
        assert(coded_data is not None)
        encrypted_data = self.env.cryptor.encrypt_data(coded_data, self.secret_key, private_key)
        assert(encrypted_data is not None)
        verifier = self.env.verifier.encode_verifier(private_key, public_key, self.secret_key)
        merged_data = self.env.verifier.merge_verifier_data(verifier, encrypted_data, self.secret_key)
        encrypted = self.env.cryptor.encrypt_global(merged_data, self.secret_key)
        return encrypted

class Context(object):
    def __init__(self, session, data):
        self.session = session
        self.data = data
