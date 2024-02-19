#!/usr/bin/python

# Copyright: (c) 2024, Proton AG
# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: rackndr_tasks
short_description: RackN Digital Rebar Tasks module
description: RackN Digital Rebar module for managing Tasks
requirements:
  - pyrackndr
extends_documentation_fragment:
  - proton.rackndr.rackndr
version_added: "0.0.2"
author:
    - Sorin Paduraru (!UNKNOWN) <spaduraru@proton.ch>
options:
    name:
        description: Task name
        required: True
        type: str
    description:
        description: Description is a one-line description of this Task
        type: str
        default: ''
    documentation:
        description:
          - Documentation should describe in detail what this task should do on
            a machine.
        type: str
        default: ''
    readonly:
        description:
          - Tracks if the store for this object is read-only.
          - This flag is informational, and cannot be changed via the API
        type: bool
        default: True
    templates:
        description:
          - Templates lists the templates that need to be rendered for the Task
          - At least Name and Contents are required
          - It is required item keys use the case expected by the API;
            otherwise module cannot achieve idempotency
        type: list
        elements: dict
        required: True
    ignore_remote_keys:
        description:
          - Ignore changes to these (remote) keys when updating the object
        type: list
        default:
          - CreatedAt
          - CreatedBy
          - LastModifiedAt
          - LastModifiedBy
    ignore_local_keys:
        description:
          - Ignore changes to these keys part of the local object when updating
            the object
        type: list
        elements: str
        default:
          - ExtraRoles
          - OutputParams
          - ExtraClaims
          - Meta
'''

EXAMPLES = r'''
# Create task containing a template
    - name: Manage tasks
      proton.rackndr.rackndr_tasks:
        name: "droopy-task"
        templates:
          - Name: step1.tmpl
            Contents: |
              #!/usr/bin/env bash
              Hello from step1.tmpl
          - Name: step2.tmpl
            Contents: |
              #!/usr/bin/env sh
              Hello from step2.tmpl
        description: "Description of droopy-task"
        documentation: "Documentation of droopy-task"
        ignore_remote_keys:
          - CreatedAt
          - CreatedBy
          - LastModifiedAt
          - LastModifiedBy
          - Meta
        rackn_role: "{{ rackn_role }}"
        rackn_user: "{{ rackn_user }}"
        rackn_pass: "{{ rackn_pass }}"
        rackn_ep: "{{ rackn_ep }}"
        rackn_ep_validate: false
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
    import pyrackndr
except ImportError:
    HAS_PYRACKNDR = False
    PYRACKNDR_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_PYRACKNDR = True
    PYRACKNDR_IMPORT_ERROR = None

# Fall-back values for the keys expected by the API when the user doesn't
# define them
TEMPLATE_DEFAULTS = {
    'Path': '',
    'ID': '',
    'Link': '',
    'Meta': {}
}


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str',
                   required=False,
                   default='present',
                   choices=['present', 'absent']),
        name=dict(type='str', required=True),
        templates=dict(type='list', elements='dict', required=True),
        description=dict(type='str', required=False, default=''),
        documentation=dict(type='str', required=False, default=''),
        readonly=dict(type='bool', required=False, default=True),
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
        ignore_local_keys=dict(
            type='list',
            required=False,
            no_log=False,
            elements='str',
            default=[
                'ExtraRoles',
                'OutputParams',
                'ExtraClaims',
                'Meta'
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
            msg=missing_required_lib('pyrackndr'),
            exception=PYRACKNDR_IMPORT_ERROR)

    data = pyrackndr.CONSTANTS['tasks'].copy()
    data['Templates'] = module.params['templates']
    data['Description'] = module.params['description']
    data['Documentation'] = module.params['documentation']
    data['Name'] = module.params['name']
    data['ReadOnly'] = module.params['readonly']

    # Set default values for Template keys missing
    for template in data['Templates']:
        enrich_template(template)

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
        'tasks'
    )
    rebar_object.dryrun = module.check_mode
    rebar_object.tls_verify = module.params['rackn_ep_validate']
    rebar_object.ignore_keys['remote'] = module.params['ignore_remote_keys']
    rebar_object.ignore_keys['local'] = module.params['ignore_local_keys']

    if module.params['state'] == 'present':
        rebar_result = rebar_object.create_or_update(module.params['name'], data)
    else:
        rebar_result = rebar_object.delete(module.params['name'])

    result = {**result, **rebar_result}

    if result['http_code'] not in [200, 201]:
        module.fail_json(msg='Uh-oh', **result)

    module.exit_json(**result)


def enrich_template(lobject):
    '''Add key/value pairs to object if key isn't present already.
    '''
    for k, v in TEMPLATE_DEFAULTS.items():
        if k not in lobject:
            lobject.update({k: v})


def main():
    run_module()


if __name__ == '__main__':
    main()
