from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):
    # RackN Digital Rebar common documentation
    DOCUMENTATION = r'''
  options:
    rackn_role:
        description: Role associated to the token requested for performing actions
        required: False
        default: superuser
    rackn_userpass:
        description:
          - user:pass credentials.
          - Used for obtaining a short-lived token used throughout the module
        fallback: RS_KEY
        required: False
        no_log: True
    rackn_user:
        description:
          - User passed to the API for obtaining a short-lived token used
            throughout the module
        fallback: RS_USER
        required: False
    rackn_pass:
        description:
          - Password passed to the API for obtaining a short-lived token used
            throughout the module
        fallback: RS_PASS
        required: False
        no_log: True
    rackn_ep:
        description: RackN Digital Rebar API endpoint
        fallback: RS_ENDPOINT
        required: True
    rackn_ep_validate:
        description:
          - RackN Digital Rebar API endpoint only accept valid TLS certificate
        fallback: RS_ENDPOINT_VALIDATE
        required: False
        default: True
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
