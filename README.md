# Ansible Collection - proton.rackndr

Define a `requirements.yml` file pointing to the collection, as
explained in the
[Ansible collection guide](https://docs.ansible.com/ansible/latest/collections_guide/collections_installing.html#install-multiple-collections-with-a-requirements-file):

```yaml
---
collections:
 - name: <repo>/proton.rackndr.git
   version: master
   type: git
```

Install and make sure the collection is available:

```sh
ansible-galaxy collection install -r requirements.yml
ansible-doc --list proton.rackndr
```
