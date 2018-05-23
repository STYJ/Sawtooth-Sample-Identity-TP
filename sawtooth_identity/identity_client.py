# Copyright 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import hashlib
import base64
from base64 import b64encode
import time
import requests
import yaml
import pickle

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader, Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList, BatchHeader, Batch

from sawtooth_identity.identity_exceptions import IdentityException

# The Transaction Family Name
FAMILY_NAME='identity'

def _sha512(data):
    return hashlib.sha512(data).hexdigest()


class IdentityClient:
    def __init__(self, base_url, keyfile=None):

        # Checks to see if keyfile is provided
        if keyfile is None:
            self._signer = None
            return

        # Base url of http address
        self._base_url = base_url

        # Open keyfile to read private key
        try:
            with open(keyfile) as fd:
                private_key_str = fd.read().strip()
        except OSError as err:
            raise IdentityException(
                'Failed to read private key {}: {}'.format(
                    keyfile, str(err)))
            return

        # Load the private key to create signer
        try:
            private_key = Secp256k1PrivateKey.from_hex(private_key_str)
        except ParseError as e:
            raise IdentityException(
                'Unable to load private key: {}'.format(str(e)))
            return
        else:
            # Creating signer with the provided private key
            self._signer = CryptoFactory(create_context('secp256k1')) \
                .new_signer(private_key)


    # For each valid cli commands in _cli.py file
    # Add methods to:
    # 1. Do any additional handling, if required
    # 2. Create a transaction and a batch
    # 3. Send to rest-api

    def create(self, name, date_of_birth, gender, auth_user=None, auth_password=None):
        return self._send_identity_txn(
            "create",
            name,
            date_of_birth=date_of_birth,
            gender=gender,
            auth_user=auth_user,
            auth_password=auth_password)

    def delete(self, name, auth_user=None, auth_password=None):
        return self._send_identity_txn(
            "delete",
            name,
            auth_user=auth_user,
            auth_password=auth_password)

    def update(self, name, parameter, value, auth_user=None, auth_password=None):
        # Retrieving the current payload with the provided name
        old_payload = self.show(name)

        if old_payload is not None:
            if parameter == 'name':
                name = value
                date_of_birth = old_payload["Date_of_birth"]
                gender = old_payload["Gender"]
            elif parameter == 'date_of_birth':
                name = name
                date_of_birth = value
                gender = old_payload["Gender"]
            elif parameter = 'gender':
                name = name
                date_of_birth = old_payload["Date_of_birth"]
                gender = value
        else:
            raise IdentityException("Invalid parameter provided: {}".format(parameter))

        # Return new payload
        return self._send_identity_txn(
            "update",
            name,
            date_of_birth,
            gender,
            auth_user=auth_user,
            auth_password=auth_password)

    # List all addresses starting with the identity prefix
    def list(self, auth_user=None, auth_password=None):
        identity_prefix = self._get_prefix()

        # this is like doing curl http://rest-api:8008/state?address=....
        # the result will be a dictionary that contains a data, head, link and paging.
        # {
        #   "data": [
        #     {
        #       "address": "1cf1261883383c17490deb88ae0423d7910dcd65e6639ebae4c3943...",
        #       "data": "oWV0aGlyZAM="
        #     },
        #     {
        #       "address": "1cf1267201e535697af914e69d6f46b2a88655c86c2371288052ccd...",
        #       "data": "oWVmaXJzdAE="
        #     },
        #     {
        #       "address": "1cf1268ab4bdd839e7c672baa6eb87e06f59b2d3a68ad0533f2a13e...",
        #       "data": "oWZzZWNvbmQC"
        #     }
        #   ],
        #   "head": "3c4960bc71ceb625ff71318aec932708046b0efd8e1a33b3229bd855d33848...",
        #   "link": "http://rest-api:8008/state?head=3c4960bc71ceb625ff71318aec9327...",
        #   "paging": {
        #     "limit": null,
        #     "start": null
        #   }
        # }
        result = self._send_request(
            "state?address={}".format(identity_prefix),
            auth_user=auth_user,
            auth_password=auth_password)

        try:
            # this will retrieve the value with the "data" key.
            encoded_entries = yaml.safe_load(result)["data"]

            return [
                # returns a list of dicts (payload)
                pickle.loads(base64.b64decode(entry["data"]))
                for entry in encoded_entries
            ]

        except BaseException:
            return None

    # Show the address that is tied to this public key
    def show(self, name, auth_user=None, auth_password=None):

        # this follows a similar format to the one above however
        # the data key has the encoded payload as its corresponding value
        # {
        #   "data": "oWV0aGlyZAM=",
        #   "head": "3c4960bc71ceb625ff71318aec932708046b0efd8e1a33b322...",
        #   "link": "http://rest-api:8008/state/1cf1261883383c17490deb8...",
        # }
        result = self._send_request(
            "state/{}".format(self._get_address(name)),
            auth_user=auth_user,
            auth_password=auth_password)

        try:
            # returns a dict (payload)
            return pickle.loads(
                base64.b64decode(
                    yaml.safe_load(result)["data"]))

        except BaseException:
            return None

    # def _get_status(self, batch_id, wait, auth_user=None, auth_password=None):
    #     try:
    #         result = self._send_request(
    #             'batch_statuses?id={}&wait={}'.format(batch_id, wait),
    #             auth_user=auth_user,
    #             auth_password=auth_password)
    #         return yaml.safe_load(result)['data'][0]['status']
    #     except BaseException as err:
    #         raise IdentityException(err)

    def _get_prefix(self):
        return _sha512(FAMILY_NAME.encode('utf-8'))[0:6]

    def _get_address(self, name):
        prefix = self._get_prefix()
        infix = _sha512(name.encode('utf-8'))[0:6]
        suffix = _sha512(self._signer.get_public_key().as_hex().encode('utf-8'))[-58:]
        return prefix + infix + suffix

    def _send_request(self,
                      suffix,
                      data=None,
                      content_type=None,
                      auth_user=None,
                      auth_password=None):
        if self._base_url.startswith("http://"):
            url = "{}/{}".format(self._base_url, suffix)
        else:
            url = "http://{}/{}".format(self._base_url, suffix)

        if auth_user is not None:
            auth_string = "{}:{}".format(auth_user, auth_password)
            b64_string = b64encode(auth_string.encode()).decode()
            auth_header = 'Basic {}'.format(b64_string)
            headers['Authorization'] = auth_header

        headers = {}
        if content_type is not None:
            headers['Content-Type'] = content_type

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if not result.ok:
                raise IdentityException("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise IdentityException(
                'Failed to connect to {}: {}'.format(url, str(err)))

        except BaseException as err:
            raise IdentityException(err)

        return result.text

    def _send_identity_txn(self,
                           action,
                           name,
                           date_of_birth='',
                           gender='',
                           # wait=None,
                           auth_user=None,
                           auth_password=None):

        # Payload is a dict with 4 key value pairs
        payload = {
            'Action': action
            'Name': name,
            'Date_of_birth': date_of_birth,
            'Gender': gender
        }

        # Serialisation is via pickle
        payload_bytes = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)

        # Construct the address
        # In this example, input and output addresses are the same
        address = self._get_address(name)

        header_bytes = TransactionHeader(

            # Public key of the client that signed this transaction
            signer_public_key=self._signer.get_public_key().as_hex(),
            family_name=FAMILY_NAME,
            family_version="0.1",
            inputs=[address],
            outputs=[address],
            dependencies=[],

            # Payload encrypted with sha512
            payload_sha512=_sha512(payload_bytes),

            # Public key of the signer that signed the batch which
            # contains this transaction
            batcher_public_key=self._signer.get_public_key().as_hex(),
            nonce=time.time().hex().encode()
        ).SerializeToString()

        # Signing this transaction
        signature = self._signer.sign(header_bytes)

        transaction = Transaction(
            header=header_bytes,
            payload=payload_bytes,
            header_signature=signature
        )

        batch_list = self._create_batch_list([transaction])
        batch_id = batch_list.batches[0].header_signature

        # If you remove the wait parameter, this section of code
        # can be removed as well.   
        # if wait and wait > 0:
        #     wait_time = 0
        #     start_time = time.time()
        #     response = self._send_request(
        #         "batches", 
        #         batch_list.SerializeToString(),
        #         'application/octet-stream',
        #         auth_user=auth_user,
        #         auth_password=auth_password)
        #     while wait_time < wait:
        #         status = self._get_status(
        #             batch_id,
        #             wait - int(wait_time),
        #             auth_user=auth_user,
        #             auth_password=auth_password)
        #         wait_time = time.time() - start_time

        #         if status != 'PENDING':
        #             return response

        #     return response

        return self._send_request(
            "batches", 
            batch_list.SerializeToString(),
            'application/octet-stream',
            auth_user=auth_user,
            auth_password=auth_password)

    def _create_batch_list(self, transactions):

        # transaction_signatures must be in the same order that is listed
        # in transactions
        transaction_signatures = [t.header_signature for t in transactions]

        header_bytes = BatchHeader(
            # Public key of the signer of this batch
            signer_public_key=self._signer.get_public_key().as_hex(),
            transaction_ids=transaction_signatures
        ).SerializeToString()

        # Signing the batch
        signature = self._signer.sign(header_bytes)

        batch = Batch(
            header=header_bytes,
            transactions=transactions,
            header_signature=signature
        )

        # In order to submit batches to validator, they must be in a BatchList
        # Multiple (optionally dependent) batches for 1 BatchList
        return BatchList(batches=[batch])
