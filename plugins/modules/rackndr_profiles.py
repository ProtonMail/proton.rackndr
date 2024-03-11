#!/usr/bin/python

# Copyright: (c) 2024, Proton AG
# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: rackndr_profiles
short_description: RackN Digital Rebar Profiles module
description: RackN Digital Rebar module for managing Profiles
requirements:
  - pyprotonrebar
extends_documentation_fragment:
  - proton.rackndr.rackndr
version_added: "0.0.3"
author:
    - Sorin Paduraru (@sorinpad) <spaduraru@proton.ch>
options:
    name:
        description:
          - The name of the profile. This must be unique across all profiles
        required: True
        type: str
    description:
        description:
          - A description of this profile. This can contain any reference
            information for humans you want associated with the profile
        required: False
        type: str
        default: ''
    documentation:
        description:
          - Documentation of this profile. This should tell what the profile is
            for, any special considerations that should be taken into account
            when using it, etc. in rich structured text (rst)
        required: False
        type: str
        default: ''
    readonly:
        description:
          - Tracks if the store for this object is read-only. This flag is
            informational, and cannot be changed via the API.
        required: False
        type: bool
        default: True
    meta:
        description:
          - Metadata associated to the profile.  JSON data passed as stripped,
            folded Multi-line YAML string
        required: False
        type: json
        default: {}
    partial:
        description:
          - Partial tracks if the object is not complete when returned.
        required: False
        type: bool
        default: False
    params:
        description:
          - Any parameters that are needed by this profile. 
        required: True
        type: json
'''

EXAMPLES = r'''
# Create a profile defining values for some params
- name: Create a profile with three params
  proton.rackndr.rackndr_profiles:
    name: database-server
    description: Profile that sets params required by a db server
    params: >-
      {
        "disk-layout": "two-disks",
        "config-server": "ansible-01",
        "network": "abc-public"
      }
    meta: >-
      {
        "color": "yellow"
      }
'''

RETURN = r'''
message:
    description: The message returned by the API.
    type: str
    returned: always
    sample: null
http_code:
    description: HTTP status code returned by the API.
    type: str
    returned: always
    sample: 200
'''

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.parameters import (
    env_fallback
)
from ansible.module_utils.basic import missing_required_lib

try:
    import pyprotonrebar.pyrackndr
except ImportError:
    HAS_PYRACKNDR = False
    PYRACKNDR_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_PYRACKNDR = True
    PYRACKNDR_IMPORT_ERROR = None


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str',
                   required=False,
                   default='present',
                   choices=['present', 'absent']),
        name=dict(type='str', required=True),
        description=dict(type='str', required=False, default=''),
        documentation=dict(type='str', required=False, default=''),
        readonly=dict(type='bool', required=False, default=True),
        meta=dict(type='json', required=False, default={}),
        params=dict(type='json', required=True),
        partial=dict(type='bool', required=False, default=False),
        ignore_remote_keys=dict(
            type='list',
            required=False,
            no_log=False,
            elements='str',
            default=[
                'CreatedAt',
                'CreatedBy',
                'LastModifiedAt',
                'LastModifiedBy',
            ]),
        rackn_role=dict(type='str',
                        required=False,
                        default='superuser'),
        rackn_userpass=dict(type='str',
                            required=False,
                            no_log=True,
                            fallback=(env_fallback, ['RS_KEY'])
                            ),
        rackn_user=dict(type='str',
                        required=False,
                        fallback=(env_fallback, ['RS_USER']),
                        ),
        rackn_pass=dict(type='str',
                        required=False,
                        fallback=(env_fallback, ['RS_PASS']),
                        no_log=True),
        rackn_ep=dict(type='str',
                      required=True,
                      fallback=(env_fallback, ['RS_ENDPOINT'])
                      ),
        rackn_ep_validate=dict(type='bool',
                               required=False,
                               fallback=(env_fallback, ['RS_ENDPOINT_VALIDATE']),
                               default=True),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_together=[
            ('rackn_user', 'rackn_pass'),
        ],
        required_one_of=[
            ('rackn_userpass', 'rackn_user'),
        ],
        mutually_exclusive=[
            ('rackn_userpass', 'rackn_user'),
        ],
        supports_check_mode=True
    )

    if not HAS_PYRACKNDR:
        module.fail_json(
            msg=missing_required_lib('pyprotonrebar'),
            exception=PYRACKNDR_IMPORT_ERROR)

    data = pyprotonrebar.CONSTANTS['profiles'].copy()
    data['Description'] = module.params['description']
    data['Documentation'] = module.params['documentation']
    data['Name'] = module.params['name']
    data['ReadOnly'] = module.params['readonly']
    data['Meta'] = json.loads(module.params['meta'])
    data['Partial'] = module.params['partial']
    data['Params'] = json.loads(module.params['params'])

    if module.params['rackn_userpass']:
        creds = f"{module.params['rackn_userpass']}"
    else:
        creds = f"{module.params['rackn_user']}:{module.params['rackn_pass']}"

    TOKEN = pyprotonrebar.pyrackndr.fetch_token_requests(
        module.params['rackn_role'],
        creds,
        module.params['rackn_ep'],
        ssl=module.params['rackn_ep_validate'])
    AUTH = TOKEN['header']

    rebar_object = pyprotonrebar.pyrackndr.RackNDr(
        module.params['rackn_ep'],
        AUTH,
        'profiles'
    )
    rebar_object.dryrun = module.check_mode
    rebar_object.tls_verify = module.params['rackn_ep_validate']
    rebar_object.ignore_keys['remote'] = module.params['ignore_remote_keys']

    if module.params['state'] == 'present':
        rebar_result = rebar_object.create_or_update(module.params['name'], data)
    else:
        rebar_result = rebar_object.delete(module.params['name'])

    result = {**result, **rebar_result}

    if result['http_code'] not in [200, 201]:
        module.fail_json(msg='Uh-oh', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
