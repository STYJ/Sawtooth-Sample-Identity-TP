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

import pickle
from sawtooth_sdk.processor.exceptions import InvalidTransaction


class IdentityPayload(object):

    def __init__(self, payload):
        try:
            # The payload is pickle encoded dictionary
            decoded_payload = pickle.loads(payload)
            action = decoded_payload["Action"]
            name = decoded_payload["Name"]
            date_of_birth = decoded_payload["Date_of_birth"]
            gender = decoded_payload["Gender"]
        except ValueError:
            raise InvalidTransaction("Invalid payload serialization")

        if not action:
            raise InvalidTransaction('Action is required')

        if action not in ('create', 'update', 'delete'):
            raise InvalidTransaction('Invalid action: {}'.format(action))

        # You can add additional validation checks here if necessary e.g.
        # if action == 'take':
        #     try:

        #         if int(space) not in range(1, 10):
        #             raise InvalidTransaction(
        #                 "Space must be an integer from 1 to 9")
        #     except ValueError:
        #         raise InvalidTransaction(
        #             'Space must be an integer from 1 to 9')

        # if action == 'take':
        #     space = int(space)

        if not name:
            raise InvalidTransaction('Name is required')

        if '|' in name:
            raise InvalidTransaction('Name cannot contain "|"')

        if not date_of_birth:
            raise InvalidTransaction('Date_of_birth is required')

        # Will not be implementing any validation checks to verify that
        # DOB is a legitimate DOB

        if not gender:
            raise InvalidTransaction('Gender is required')
            
        # Maybe gender validation may not really be necessary in this day and age
        if gender not in ('m', 'f', 'M', 'F', 'male', 'female', 'Male', 'Female'):
            raise InvalidTransaction('Invalid gender: {}'.format(action))

        self._action = action
        self._name = name
        self._date_of_birth = date_of_birth
        self._gender = gender

    @staticmethod
    def from_bytes(payload):
        return IdentityPayload(payload=payload)

    @property
    def action(self):
        return self._action

    @property
    def name(self):
        return self._name

    @property
    def date_of_birth(self):
        return self._date_of_birth

    @property
    def gender(self):
        return self._gender    
