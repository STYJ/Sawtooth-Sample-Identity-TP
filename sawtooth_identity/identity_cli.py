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

from __future__ import print_function
import argparse
import getpass
import logging
import os
import traceback
import sys
import pkg_resources

from colorlog import ColoredFormatter

from sawtooth_identity.identity_client import IdentityClient
from sawtooth_identity.identity_exceptions import IdentityException


DISTRIBUTION_NAME = 'sawtooth-identity'

# DEFAULT_URL = 'http://rest-api:8008'
DEFAULT_URL = 'http://127.0.0.1:8008'

def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)

    if verbose_level == 0:
        clog.setLevel(logging.WARN)
    elif verbose_level == 1:
        clog.setLevel(logging.INFO)
    else:
        clog.setLevel(logging.DEBUG)

    return clog

def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))


def create_parent_parser(prog_name):
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)
    parent_parser.add_argument(
        '-v', '--verbose',
        action='count',
        help='enable more verbose output')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser

def create_parser(prog_name):
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to create digital identities.',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    subparsers.required = True

    add_create_parser(subparsers, parent_parser)
    add_delete_parser(subparsers, parent_parser)
    add_update_parser(subparsers, parent_parser)
    add_list_parser(subparsers, parent_parser)
    add_show_parser(subparsers, parent_parser)

    return parser

def add_create_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'create',
        help='Creates a new identity',
        description='Create a new identity for the specified user / private'
        ' key. Please provide the following: <name>, <date_of_birth> and'
        ' <gender>.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='Name of this identity')

    parser.add_argument(
        'date_of_birth',
        type=str,
        help='Date of birth of this identity')

    parser.add_argument(
        'gender',
        type=str,
        help='Gender of this identity')

    # unlike the simplewallet-cli file, we don't have a parameter for
    # the user / private key because we are specifying user via the 
    # --username argument.

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

def do_create(args):
    name, date_of_birth, gender = args.name, args.date_of_birth, args.gender

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = IdentityClient(base_url=url, keyfile=keyfile)

    response = client.create(
        name,
        date_of_birth=date_of_birth,
        gender=gender,
        auth_user=auth_user,
        auth_password=auth_password)

    print("Response: {}".format(response))

def add_delete_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'delete',
        help='Deletes an existing identity',
        description='Delete an existing identity for the specified user /'
        ' private key. Please provide the following: <name>.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='name of the identity to be deleted')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

def do_delete(args):
    name = args.name

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = IdentityClient(base_url=url, keyfile=keyfile)

    response = client.delete(
        name,
        auth_user=auth_user,
        auth_password=auth_password)    

    print("Response: {}".format(response))

def add_update_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'update',
        help='Updates an existing identity',
        description='Update an existing identity for the specified user /'
        ' private key. Please provide the following: <name>, <parameter>,'
        ' <value>.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='Name of this identity')

    parser.add_argument(
        'parameter',
        type=str,
        help='Parameter to be updated')

    parser.add_argument(
        'value',
        type=str,
        help='Update the parameter with this value')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

def do_update(args):
    name, parameter, value = args.name, args.parameter, args.value

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = IdentityClient(base_url=url, keyfile=keyfile)

    response = client.update(
        name,
        parameter,
        value,
        auth_user=auth_user,
        auth_password=auth_password)

    print("Response: {}".format(response))

def add_list_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'list',
        help='Displays information for all identities',
        description='Displays information for all identities in state, showing '
        'the <name>, <date_of_birth> and <gender> for each identity.',
        parents=[parent_parser])

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

def do_list(args):
    url = _get_url(args)
    auth_user, auth_password = _get_auth_info(args)

    client = IdentityClient(base_url=url, keyfile=None)
    identities = client.list(auth_user, auth_password)

    for identity in identities:
        # this will print out 4 key-value pairs representing the action, name, DOB, gender
        for key, value in identity.items():
            print('{}: {}'.format(key, value))

def add_show_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'show',
        help='Displays information about an identity',
        description='Displays information for the identity with <name>,'
        ' showing the <name>, <date_of_birth> and <gender>.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='name of the identity to show')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

def do_show(args):
    name = args.name
    url = _get_url(args)
    auth_user, auth_password = _get_auth_info(args)

    client = IdentityClient(base_url=url, keyfile=None)
    identity = client.show(name, auth_user=auth_user, auth_password=auth_password)

    for key, value in identity.items():
            print('{}: {}'.format(key, value))


# might need this for update, add the corresponding parser and add it into
# the create_parser function on top.

# def do_take(args):
#     name = args.name
#     space = args.space

#     url = _get_url(args)
#     keyfile = _get_keyfile(args)
#     auth_user, auth_password = _get_auth_info(args)

#     client = XoClient(base_url=url, keyfile=keyfile)

#     if args.wait and args.wait > 0:
#         response = client.take(
#             name, space, wait=args.wait,
#             auth_user=auth_user,
#             auth_password=auth_password)
#     else:
#         response = client.take(
#             name, space,
#             auth_user=auth_user,
#             auth_password=auth_password)

#     print("Response: {}".format(response))


# You can change the DEFAULT_URL constant above so you don't have to keep
# type --url=http://rest-api:8008
def _get_url(args):
    return DEFAULT_URL if args.url is None else args.url

# get keyfile of the mentioned user otherwise defaults to the current user

# Note you don't really need to pass in all args, just args.username will do 
# i.e. def _get_keyfile(username) and when this method is being called, you
# pass args.username. 
def _get_keyfile(args):
    username = getpass.getuser() if args.username is None else args.username
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, username)

# Only the XO file has this function so done.
def _get_auth_info(args):
    auth_user = args.auth_user
    auth_password = args.auth_password
    if auth_user is not None and auth_password is None:
        auth_password = getpass.getpass(prompt="Auth Password: ")

    return auth_user, auth_password

def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    if args.verbose is None:
        verbose_level = 0
    else:
        verbose_level = args.verbose

    setup_loggers(verbose_level=verbose_level)

    if args.command == 'create':
        do_create(args)
    elif args.command == 'list':
        do_list(args)
    elif args.command == 'show':
        do_show(args)
    elif args.command == 'delete':
        do_delete(args)
    else:
        raise IdentityException("invalid command: {}".format(args.command))

def main_wrapper():
    try:
        main()
    except IdentityException as err:
        print("Error: {}".format(err), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
