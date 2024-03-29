#!/usr/bin/python

# Copyright: (c) 2024, Proton AG
# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: rackndr_templates
short_description: RackN Digital Rebar Templates module
description: RackN Digital Rebar module for managing Templates
requirements:
  - pyprotonrebar
extends_documentation_fragment:
  - proton.rackndr.rackndr
version_added: "0.0.1"
author:
    - Sorin Paduraru (!UNKNOWN) <spaduraru@proton.ch>
options:
    name:
        description: Template name
        required: True
        type: str
    description:
        description: A description of this template
        default: ''
        required: False
        type: str
    readonly:
        description:
          - Tracks if the store for this object is read-only.
          - This flag is informational, and cannot be changed via the API
        required: False
        type: bool
        default: True
    contents:
        description:
          - Template contents; multi-line YAML content expected
        required: True
        type: str
    diff_template_contents:
        description:
           - Show the diffs in the contents key, as opposed to showing diffs
             of the Digital Rebar template object
        required: False
        type: bool
        default: True
'''

EXAMPLES = r'''
# Create template containing a simple shell script, show diffs of contents key
- name: Create Digital Rebar Template made out of shell script
  proton.rackndr.rackndr_templates:
    name: call_script.tmpl
    state: present
    contents: |-
      #!/bin/sh
      echo 'Hello world'
    description: Simple script that outputs Hello world
    rackn_role: 'superuser'
    rackn_user: rocketskates
    rackn_pass: "{{ vault_rackn_pass }}"
    rackn_ep: "https://localhost:8092"
    rackn_ep_validate: false

# Create template, show diffs of Template object, pick-up connection details from the environment
- name: Create Digital Rebar Template made out of shell script
  proton.rackndr.rackndr_templates:
    name: simple-template
    contents: |-
      This is the template content
    description: Simple script that does nothing (probably generates errors)
    diff_template_contents: false
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
        contents=dict(type='str', required=True),
        description=dict(type='str', required=False, default=''),
        readonly=dict(type='bool', required=False, default=True),
        diff_template_contents=dict(type='bool', required=False, default=True),
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

    data = pyprotonrebar.CONSTANTS['templates'].copy()
    data['Contents'] = module.params['contents']
    data['Description'] = module.params['description']
    data['ID'] = module.params['name']
    data['ReadOnly'] = module.params['readonly']

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
        'templates'
    )
    rebar_object.dryrun = module.check_mode
    rebar_object.tls_verify = module.params['rackn_ep_validate']
    rebar_object.ignore_keys['remote'] = module.params['ignore_remote_keys']

    if module.params['state'] == 'present':
        rebar_result = rebar_object.create_or_update(module.params['name'], data)
    else:
        rebar_result = rebar_object.delete(module.params['name'])

    # Disclaimer: opinion ahead:
    # The most important piece of a template object is its contents; choose if
    # we should display the Template object diff or the Contents key diff
    if (module.params['diff_template_contents'] and 'diff' in rebar_result.keys()):
        try:
            # Creating a new object yields an empty before key
            rebar_result['diff']['before'] = rebar_result['diff']['before']['Contents']
        except TypeError:
            rebar_result['diff']['before'] = None

        if module.params['state'] == 'absent':
            rebar_result['diff']['after'] = None
        else:
            rebar_result['diff']['after'] = rebar_result['diff']['after']['Contents']
    # When interested in Template object diff, replace the Contents key for
    # easy diff-ing of the rest of the Template object keys
    elif ((not module.params['diff_template_contents']) and 'diff' in rebar_result.keys()):
        # Creating a new template results in Contents being non-existent
        try:
            rebar_result['diff']['before']['Contents'] = 'REDACTED BY MODULE FOR EASY DIFF'
        except TypeError:
            pass
        rebar_result['diff']['after']['Contents'] = 'REDACTED BY MODULE FOR EASY DIFF'

    result = {**result, **rebar_result}

    if result['http_code'] not in [200, 201]:
        module.fail_json(msg='Uh-oh', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
