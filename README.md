# workstation-setup

[pyinfra](https://pyinfra.com/) deploy file for provisioning workstations.

This deploy file targets Ubuntu 21.04. To provision a newly installed machine,
run `./bootstrap.sh`. After this initial bootstrapping, you can reprovision the
machine with `pyinfra @local deploy.py`.
