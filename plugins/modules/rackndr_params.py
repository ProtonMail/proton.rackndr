#!/usr/bin/python

# Copyright: (c) 2024, Proton AG
# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: rackndr_params
short_description: RackN Digital Rebar Params module
description: RackN Digital Rebar module for managing Params
requirements:
  - pyrackndr
extends_documentation_fragment:
  - proton.rackndr.rackndr
version_added: "0.0.1"
attributes:
  check_mode:
    support: Full
  diff_mode:
    support: Full
author:
    - Sorin Paduraru (spaduraru@proton.ch)
options:
    name:
        description:
          - Name is the name of the param. Params must be uniquely named.
        required: True
        type: str
    state:
        description: State of the param.
        required: False
        type: str
        default: present
        choices: present, absent
    description:
        description:
          - A one-line description of the parameter.
        required: False
        type: str
        default: ''
    documentation:
        description:
          - Details what the parameter does, what values it can take, what it
            is used for, etc.
        required: False
        type: str
        default: ''
    readonly:
        description:
          - Tracks if the store for this object is read-only. This flag is
            informational, and cannot be changed via the API.
        required: False
        type: bool
        default: False
    secure:
        description:
          - Secure implies that any API interactions with this Param will deal
            with SecureData values.
          - schema's of type 'string' values are masked when 'secure' is True
        required: True
        type: bool
    meta:
        description:
          - Metadata associated to the param.  JSON data passed as stripped,
            folded Multi-line YAML string
        required: False
        type: json
        default: {}
    schema:
        description:
          - Schema of the param.  JSON data passed as stripped, folded
            Multi-line YAML string
        required: True
        type: json
'''

EXAMPLES = r'''
# Create a string type param with a blue icon
- name: Create a string param
  proton.rackndr.rackndr_params:
    name: blue-param
    secure: False
    schema: >-
      {
        "type": "string"
      }
    meta: >-
      {
        "color": "blue"
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

import pyrackndr

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.parameters import (
    env_fallback
)


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
        readonly=dict(type='bool', required=False, default=False),
        secure=dict(type='bool', required=True),
        schema=dict(type='json', required=True),
        meta=dict(type='json', required=False, default={}),
        ignore_remote_keys=dict(type='list', required=False, default=[
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


    # Implicitly mask `default` value when the parameter is marked as secure
    # As a fallback, if the `default` key is not provided, mask all values
    if module.params['secure']:
        try:
            if json.loads(module.params['schema'])['type'] == 'string':
                module.no_log_values.add(json.loads(module.params['schema'])['default'])
        except KeyError:
            for i in json.loads(module.params['schema']).values():
                module.no_log_values.add(i)


    data = pyrackndr.CONSTANTS['params'].copy()
    data['Description'] = module.params['description']
    data['Documentation'] = module.params['documentation']
    data['Name'] = module.params['name']
    data['ReadOnly'] = module.params['readonly']
    data['Meta'] = json.loads(module.params['meta'])
    data['Schema'] = json.loads(module.params['schema'])
    data['Secure'] = module.params['secure']

    if module.params['rackn_userpass']:
        creds = f"{module.params['rackn_userpass']}"
    else:
        creds = f"{module.params['rackn_user']}:{module.params['rackn_pass']}"

    TOKEN = pyrackndr.pyrackndr.fetch_token_requests(
        module.params['rackn_role'],
        creds,
        module.params['rackn_ep'],
        ssl=module.params['rackn_ep_validate'])
    AUTH = TOKEN['header']

    rebar_object = pyrackndr.pyrackndr.RackNDr(
        module.params['rackn_ep'],
        AUTH,
        'params'
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
