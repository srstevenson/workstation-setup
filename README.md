# pyinfra-deploy

[pyinfra](https://pyinfra.com/) deploy file for provisioning workstations and
VMs.

This deploy file targets Ubuntu 20.10. To provision a newly installed machine,
run `./bootstrap.sh`. After this initial bootstrapping, you can reprovision the
machine with `pyinfra @local deploy.py`.
