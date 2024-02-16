#!/usr/bin/python

# Copyright: (c) 2024, Proton AG
# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: rackndr_subnets
short_description: RackN Digital Rebar Subnet module
description: RackN Digital Rebar module for managing Subnets
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
        description: Name of the subnet. Subnet names must be unique
        required: true
        type: str
    state:
        description: State of the subnet
        required: False
        type: str
        default: present
        choices: present, absent
    description:
        description:
          - A description of this Subnet.  This should tell what it is for, any
            special considerations that should be taken into account when using
            it, etc.
        required: False
        type: str
    enabled:
        description:
          - Indicates if the subnet should hand out leases or continue
            operating leases if already running
        required: False
        type: bool
        default: True
    active_start:
        description:
          - First non-reserved IP address we will hand non-reserved leases from
        required: True
        type: str
    active_end:
        description:
          - Last non-reserved IP address we will hand non-reserved leases from
        required: True
        type: str
    active_lease_time:
        description:
          - Default lease duration in seconds we will hand out to leases that
            do not have a reservation
        required: True
        type: int
    reserved_lease_time:
        description:
          - Default lease time we will hand out to leases created from a
            reservation in our subnet
        required: False
        type: int
        default: 21600
    netmask:
        description: Network mask associated with the subnet
        required: True
        type: str
    network:
        description: Network associated with the subnet
        required: True
        type: str
    gateway:
        description: Gateway associated with the subnet
        required: True
        type: str
    dns_server:
        description: DNS resolver associated with the subnet
        required: True
        type: str
'''

EXAMPLES = r'''
# Create a subnet; connection details pulled from environment
- name: Create a subnet
  proton.rackndr.rackndr_subnets:
    name: ProvisionSubnet
    description: A subnet used for provisioning machines
    active_start: "192.168.0.10"
    active_end: "192.168.0.25"
    active_lease_time: "8600"
    reserved_lease_time: "21600"
    netmask: "255.255.255.0"
    gateway: "192.168.0.1"
    dns_server: "192.168.0.200"
    network: "192.168.0.0"
    domain_name: "provision.lan"
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

import ipaddress

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
        enabled=dict(type='bool', required=False, default=True),
        active_start=dict(type='str', required=True),
        active_end=dict(type='str', required=True),
        active_lease_time=dict(type='int', required=True),
        reserved_lease_time=dict(type='int', required=False, default=21600),
        netmask=dict(type='str', required=True),
        gateway=dict(type='str', required=True),
        dns_server=dict(type='str', required=True),
        network=dict(type='str', required=True),
        domain_name=dict(type='str', required=True),
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


    data = pyrackndr.CONSTANTS['subnets'].copy()
    data['ActiveEnd'] = module.params['active_end']
    data['ActiveLeaseTime'] = module.params['active_lease_time']
    data['ActiveStart'] = module.params['active_start']
    data['Description'] = module.params['description']
    data['Enabled'] = module.params['enabled']
    data['Name'] = module.params['name']
    data['Options'][0]['Value'] = module.params['gateway']
    data['Options'][1]['Value'] = module.params['dns_server']
    data['Options'][2]['Value'] = module.params['domain_name']
    data['Options'][3]['Value'] = module.params['netmask']
    data['Options'][4]['Value'] = str(ipaddress.ip_network(
        f"{module.params['network']}/{module.params['netmask']}"
    ).broadcast_address)
    data['ReservedLeaseTime'] = module.params['reserved_lease_time']
    data['Subnet'] = str(ipaddress.ip_network(
        f"{module.params['network']}/{module.params['netmask']}"
    ).with_prefixlen)

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
        'subnets'
    )
    rebar_object.dryrun = module.check_mode
    rebar_object.tls_verify = module.params['rackn_ep_validate']

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
