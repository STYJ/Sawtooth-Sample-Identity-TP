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

import sys
import os
import argparse
import pkg_resources

# Adding the necessary path to PYTHONPATH
path = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.append(path)

from sawtooth_sdk.processor.core import TransactionProcessor
from sawtooth_sdk.processor.log import init_console_logging
from sawtooth_sdk.processor.log import log_configuration
from sawtooth_sdk.processor.config import get_log_config
from sawtooth_sdk.processor.config import get_log_dir
from sawtooth_sdk.processor.config import get_config_dir
from sawtooth_identity.processor.handler import IdentityTransactionHandler
from sawtooth_identity.processor.config.identity import IdentityConfig
from sawtooth_identity.processor.config.identity import \
    load_default_identity_config
from sawtooth_identity.processor.config.identity import \
    load_toml_identity_config
from sawtooth_identity.processor.config.identity import \
    merge_identity_config


DISTRIBUTION_NAME = 'sawtooth-identity'


def parse_args(args):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '-C', '--connect',
        help='Endpoint for the validator connection')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Increase output sent to stderr')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='print version information')

    return parser.parse_args(args)


def load_identity_config(first_config):
    default_identity_config = \
        load_default_identity_config()
    conf_file = os.path.join(get_config_dir(), 'identity.toml')

    toml_config = load_toml_identity_config(conf_file)

    return merge_identity_config(
        configs=[first_config, toml_config, default_identity_config])


def create_identity_config(args):
    return IdentityConfig(connect=args.connect)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = parse_args(args)
    processor = None
    try:
        arg_config = create_identity_config(opts)
        identity_config = load_identity_config(arg_config)
        processor = TransactionProcessor(url=identity_config.connect)
        log_config = get_log_config(filename="identity_log_config.toml")

        # If no toml, try loading yaml
        if log_config is None:
            log_config = get_log_config(filename="identity_log_config.yaml")

        if log_config is not None:
            log_configuration(log_config=log_config)
        else:
            log_dir = get_log_dir()
            # use the transaction processor zmq identity for filename
            log_configuration(
                log_dir=log_dir,
                name="identity-" + str(processor.zmq_id)[2:-1])

        init_console_logging(verbose_level=opts.verbose)

        handler = identityTransactionHandler()

        processor.add_handler(handler)
        print("got here fine")
        processor.start()
        print("what happened?")
    except KeyboardInterrupt:
        pass
    except Exception as e:  # pylint: disable=broad-except
        print("Error: {}".format(e))
    finally:
        if processor is not None:
            print("stopping")
            processor.stop()
