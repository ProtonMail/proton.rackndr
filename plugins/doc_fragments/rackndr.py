from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):
    # RackN Digital Rebar common documentation
    DOCUMENTATION = r'''
  options:
    state:
        description: State of the resource.
        required: False
        type: str
        default: "present"
        choices: ["present", "absent"]
    rackn_role:
        description: Role associated to the token requested for performing actions
        required: False
        default: "superuser"
        type: str
    rackn_userpass:
        description:
          - user:pass credentials.
          - Used for obtaining a short-lived token used throughout the module
        fallback: RS_KEY
        required: False
        no_log: True
        type: str
    rackn_user:
        description:
          - User passed to the API for obtaining a short-lived token used
            throughout the module
        fallback: RS_USER
        required: False
        type: str
    rackn_pass:
        description:
          - Password passed to the API for obtaining a short-lived token used
            throughout the module
        fallback: RS_PASS
        required: False
        no_log: True
        type: str
    rackn_ep:
        description: RackN Digital Rebar API endpoint
        fallback: RS_ENDPOINT
        required: True
        type: str
    rackn_ep_validate:
        description:
          - RackN Digital Rebar API endpoint only accept valid TLS certificate
        fallback: RS_ENDPOINT_VALIDATE
        required: False
        default: True
        type: bool
    ignore_remote_keys:
        description:
          - Ignore changes to these (remote) keys when updating the object
        type: list
        default:
          - CreatedAt
          - CreatedBy
          - LastModifiedAt
          - LastModifiedBy
'''
