# Copyright 2016-2018 Intel Corporation
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

import logging
import pickle

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError

from sawtooth_identity.processor.identity_payload import IdentityPayload
from sawtooth_identity.processor.identity_state import Identity
from sawtooth_identity.processor.identity_state import IdentityState
from sawtooth_identity.processor.identity_state import IDENTITY_NAMESPACE


LOGGER = logging.getLogger(__name__)


class IdentityTransactionHandler(TransactionHandler):

    @property
    def family_name(self):
        return 'identity'

    @property
    def family_versions(self):
        return ['0.1']

    @property
    def namespaces(self):
        return [IDENTITY_NAMESPACE]

    def apply(self, transaction, context):

        header = transaction.header
        signer = header.signer_public_key

        # Unpack transaction
        # returns an IdentityPayload object that contain action, name
        # date_of_birth and gender
        identity_payload = IdentityPayload.from_bytes(transaction.payload)

        # Retrieve state from context
        identity_state = IdentityState(context)

        # Process transaction and save updated state data
        action = identity_payload.action

        # Checks if it's a valid action
        if action not in ('create', 'delete', 'update'):
            raise InvalidTransaction('Unhandled action: {}'.format(
                action))

        # could use a variable name = identity_payload.name
        identity = identity_state.get_identity(identity_payload.name)
        
        if action == 'delete':

            if identity is None:
                raise InvalidTransaction(
                    'Invalid action: name does not exist')

            identity_state.delete_identity(identity)

        elif action == 'create':

            # Identity has been created before
            # Logic may need fixing
            if identity is not None:
                raise InvalidTransaction(
                    'Invalid action: Identity already exists: {}'.format(
                        identity_payload.name))

            identity = Identity(
                name=identity_payload.name,
                date_of_birth=identity_payload.date_of_birth,
                gender=identity_payload.gender)

            identity_state.set_identity(identity_payload.name, identity)
            _display("Player {} created a new identity.".format(signer[:6]))

        elif action == 'update':

            if identity is None:
                raise InvalidTransaction(
                    'Invalid action: Update requires an existing identity')

            if identity.owner != signer:
                raise InvalidTransaction(
                    "This identity does not belong to this user:" +
                    " {}".format(signer[:6]))

            # I don't believe there are any other validations required 
            # as they're all built elsewhere.

            # The update transaction that is received by the CLI has 
            # already been manipulated, see identity_client.py.
            identity = _update_identity(identity, identity_payload)
            identity_state.set_identity(identity_payload.name, identity)
            _display("User {} has updated identity with the name {}."
                .format(signer[:6], identity_payload.name))

def _update_identity(identity, payload):
    identity.name = payload.name
    identity.date_of_birth = payload.date_of_birth
    identity.gender = payload.gender

def _display(msg):
    n = msg.count("\n")

    if n > 0:
        msg = msg.split("\n")
        length = max(len(line) for line in msg)
    else:
        length = len(msg)
        msg = [msg]

    # pylint: disable=logging-not-lazy
    LOGGER.debug("+" + (length + 2) * "-" + "+")
    for line in msg:
        LOGGER.debug("+ " + line.center(length) + " +")
    LOGGER.debug("+" + (length + 2) * "-" + "+")
