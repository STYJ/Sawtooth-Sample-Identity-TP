# Copyright 2017 Intel Corporation
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

from sawtooth_processor_test.message_factory import MessageFactory

class IdentityMessageFactory:
    # done
    def __init__(self, signer=None):
        self._factory = MessageFactory(
            family_name="identity",
            family_version="0.1",
            namespace=MessageFactory.sha512("identity".encode("utf-8"))[0:6],
            signer=signer)

    # done
    def get_public_key(self):
        return self._factory.get_public_key()

    # done
    def _name_to_address(self, name):
        return self._factory.namespace + \
            self._factory.sha512(name.encode())[0:6] + \
            self._factory.sha512(game.encode())[-58:]

    # done
    def create_tp_register(self):
        return self._factory.create_tp_register()

    # done
    def create_tp_response(self, status):
        return self._factory.create_tp_response(status)

    # done
    def _dumps(self, obj):
        return cbor.dumps(obj)

    # done
    def _loads(self, data):
        return cbor.loads(data)

    # done
    def _create_txn(self, txn_function, action, name, date_of_birth='', gender=''):
        payload = {
            'Action': action
            'Name': name,
            'Date_of_birth': date_of_birth,
            'Gender': gender
        }

        payload_bytes = self._dumps(payload)
        addresses = [self._name_to_address(name)]

        return txn_function(payload_bytes, addresses, addresses, [])

    # done
    def create_tp_process_request(self, action, name, date_of_birth='', gender=''):
        txn_function = self._factory.create_tp_process_request
        return self._create_txn(txn_function, action, name, date_of_birth, gender)

    # done
    def create_transaction(self, action, name, date_of_birth='', gender=''):
        txn_function = self._factory.create_transaction
        return self._create_txn(txn_function, action, name, date_of_birth, gender)

    # done
    def create_get_request(self, name):
        addresses = [self._name_to_address(name)]
        return self._factory.create_get_request(addresses)

    # done
    # Not really sure about this 
    def create_get_response(self, name, date_of_birth, gender):
        address = self._name_to_address(name)

        data = None
        if date_of_birth is not None and gender is not None:
            data = self._dumps({"Name": name, "Date_of_birth": date_of_birth, "Gender": gender})
        else:
            data = None

        return self._factory.create_get_response({address: data})

    # done
    def create_set_response(self, name):
        addresses = [self._name_to_address(name)]
        return self._factory.create_set_response(addresses)

    # done
    # Not really sure about this
    def create_set_request(self, name, date_of_birth, gender):
        address = self._name_to_address(name)

        if date_of_birth is not None and gender is not None:
            data = self._dumps({"Name": name, "Date_of_birth": date_of_birth, "Gender": gender})
        else:
            data = None

        return self._factory.create_set_request({address: data})




