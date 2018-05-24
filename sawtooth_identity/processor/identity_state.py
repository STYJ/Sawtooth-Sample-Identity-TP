# Copyright 2018 Intel Corporation
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
# -----------------------------------------------------------------------------

import hashlib
import pickle
from sawtooth_sdk.processor.exceptions import InternalError


IDENTITY_NAMESPACE = hashlib.sha512('identity'.encode("utf-8")).hexdigest()[0:6]


infix = _sha512(name.encode('utf-8'))[0:6]
        suffix = _sha512(self._signer.get_public_key().as_hex().encode('utf-8'))[-58:]

def _make_identity_address(self, name):
    return IDENTITY_NAMESPACE + \
        hashlib.sha512(name.encode('utf-8')).hexdigest()[0:6] + \
        hashlib.sha512(self._signer.get_public_key().as_hex().encode('utf-8'))[-58:]


class Identity(object):
    def __init__(self, name, date_of_birth, gender):
        self.name = name
        self.date_of_birth = date_of_birth
        self.gender = gender
        self._owner = self._signer.get_public_key().as_hex()

    @property
    def owner(self):
        return self._owner
    

class IdentityState(object):

    TIMEOUT = 3

    def __init__(self, context):
        """Constructor.

        Args:
            context (sawtooth_sdk.processor.context.Context): Access to
                validator state from within the transaction processor.
        """

        # context refers to the validator state.
        self._context = context

        # The IdentityState has its own cache for optimisation to reduce number
        # of REST api calls. Cache = {Address: serialized state data}
        self._address_cache = {}

    # loads the identity with the name name
    def get_identity(self, name):
        """Get the identity associated with name.

        Args:
            name (str): The name.

        Returns:
            (identity): All the information specifying a identity.
        """

        # dict.get("key") is equivalent to dict["key"]
        # this should return you a Identity object
        return self._load_identities(name=name).get(name)

    # delete the identity with the name name
    def delete_identity(self, name):
        """Delete the identity named name from state.

        Args:
            name (str): The name.

        Raises:
            KeyError: The identity with name does not exist.
        """

        identities = self._load_identities(name=name)

        # delete identity from dict of name, identity pairs
        try:
            del identities[name]
        except KeyError:
            raise InternalError("The identity with name {} does not exist.".format(name))

        # If identities is not empty
        if identities:

            # update address cache and validator state to reflect remaining identities
            # that said, it feels weird to store on the _address_cache 
            # deleted_name, remaining identities pair since deleted_name
            self._store_identity(name, identities=identities)
        else:

            # Remove from address cache and validator state
            self._delete_identity(name)

    # add / update the identity with the name name
    def set_identity(self, name, identity):
        """Store the identity in the validator state.

        Args:
            name (str): The name.
            identity (identity): The information specifying the current identity.
        """

        identities = self._load_identities(name=name)

        identities[name] = identity

        self._store_identity(name, identities=identities)

    def _store_identity(self, name, identities):
        address = _make_identity_address(self, name)

        state_data = self._serialize(identities)

        # add to address cache for the IdentityState object
        self._address_cache[address] = state_data

        # add into the validator's state
        self._context.set_state(
            {address: state_data},
            timeout=self.TIMEOUT)

    def _delete_identity(self, name):
        address = _make_identity_address(self, name)

        # remove from address cache for the IdentityState object
        self._address_cache[address] = None

        # remove from the validator's state
        self._context.delete_state(
            [address],
            timeout=self.TIMEOUT)

    def _load_identities(self, name):

        # gets the address of identity with name name
        address = _make_identity_address(self, name)

        # Checks if address is a valid key the cache (dict)
        if address in self._address_cache:

            # retrieve the serialized identities
            serialized_identities = self._address_cache[address]

            # deserialize and return
            identities = self._deserialize(data=serialized_identities)

        # If address cannot be found in cache, look at context (validator state)
        else:

            state_entries = self._context.get_state(
                [address],
                timeout=self.TIMEOUT)

            # If something was retrieved from validator state, update cache
            if state_entries:

                # Extract the identities
                serialized_identities = state_entries[0].data

                # Update cache
                self._address_cache[address] = serialized_identities

                # Deserialize it and return it
                identities = self._deserialize(data=serialized_identities)

            else:

                # I believe this is what the address_cache and validator state
                # doesn't contain anything wrt this identity, something like
                # brand new txn.
                self._address_cache[address] = None
                identities = {}

        return identities

    def _deserialize(self, data):
        """Take bytes stored in state and deserialize them into Python
        identity objects.

        Args:
            data (bytes): The pickle encoded identity stored in state.

        Returns:
            (dict): identity name (str) keys, identity values.
        """

        identities = {}
        try:
            for identity in pickle.loads(data):
                name = identity.name
                identities[name] = identity
        except ValueError:
            raise InternalError("Failed to deserialize xidentity data")

        return identities

    def _serialize(self, identities):
        """Takes a dict of identity objects, convert into an array
        before serializing the entire array into bytes all together.

        Args:
            identities (dict): identity name (str) keys, identity values.

        Returns:
            (bytes): The pickle encoded identity stored in state.
        """

        serialized_identities = []
        for _, identity in identities.items():
            serialized_identities.append(identity)

        return pickle.dumps(serialized_identity, protocol=pickle.HIGHEST_PROTOCOL)
