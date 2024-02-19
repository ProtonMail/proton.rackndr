from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):
    # RackN Digital Rebar common documentation
    DOCUMENTATION = r'''
  attributes:
    check_mode:
      support: full
      description: Can run in check mode and return predicted changed status
    diff_mode:
      support: full
      description: Returns diff between local and remote object

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
          - Used for obtaining a short-lived token used throughout the module.
          - If not specified, the value of the E(RS_KEY) environment variable,
            if any, is used.
        required: False
        type: str
    rackn_user:
        description:
          - User passed to the API for obtaining a short-lived token used
            throughout the module.
          - If not specified, the value of the E(RS_USER) environment variable,
            if any, is used.
        required: False
        type: str
    rackn_pass:
        description:
          - Password passed to the API for obtaining a short-lived token used
            throughout the module
          - If not specified, the value of the E(RS_PASS) environment variable,
            if any, is used.
        required: False
        type: str
    rackn_ep:
        description:
          - RackN Digital Rebar API endpoint
          - The value of the E(RS_ENDPOINT) environment variable, if any, is
            used.
        required: True
        type: str
    rackn_ep_validate:
        description:
          - RackN Digital Rebar API endpoint only accept valid TLS certificate
          - The value of the E(RS_ENDPOINT_VALIDATE) environment variable, if
            any, is used.
        required: False
        default: True
        type: bool
    ignore_remote_keys:
        description:
          - Ignore changes to these (remote) keys when updating the object
        type: list
        elements: str
        default:
          - CreatedAt
          - CreatedBy
          - LastModifiedAt
          - LastModifiedBy
'''
