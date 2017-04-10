This directory contain tools for call VMware vSphere API.

1. summary_resourcepool_win_os.py
    - This tool for gather vSphere VM CPU, RAM, OS (by vSphere VM setting), top resource pools, actual last hour CPU usage, actual last hour RAM usage and custom VM attribute "SPLA_LICENED_WINDOWS" (can change on util.py) status.
    - I use this for count Microsoft SPLA license by detect the OS type and VM attribute.
    - Dependency
         - util.py (this project)
         - XlsxWriter==0.9.6
         - pyvmomi==6.5
         - futures==3.0.4
    - The GID means group ID, I use that for different group counting and resource allocate on cluster.
         
1. drs_rule_for_windows_vm.py
    - This tool for check VM's attribute "SPLA_LICENED_WINDOWS" (can change on util.py) and ESXi host's attribute "SPLA_LICENED_HOST" (can change on util.py). then create DRS group for VMs and hosts, and apply to a DRS rule. To enforce those VM must run on host with attribute value.
    - The value of "SPLA_LICENED_WINDOWS", "SPLA_LICENED_HOST" and "LICENSED_WINDOWS_FIELD_VALUE" is store on util.py
    - Dependency
        - util.py (this project)
        - pyvmomi==6.5
1. vsphere_login.txt
    - Store vSphere information. Included Name (for reporting only), vSphere address, vSphere login and vSphere password
    - start with '#' is comment
    - 1 record per line
    
    
Tested on vCenter 5.5 and 6.0.