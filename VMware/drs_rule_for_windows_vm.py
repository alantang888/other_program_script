import logging
import logging.handlers
import time

from pyVim import connect
from pyVmomi import vim

from util import get_all_vm_under_folder, get_cluster, get_attribute_key_by_name, SPLA_LICENSED_HOST_FIELD_NAME, \
    LICENSED_WINDOWS_FIELD_NAME, LICENSED_WINDOWS_FIELD_VALUE, get_vsphere_config

DRS_VM_GROUP_NAME = "Windows VM"
DRS_HOST_GROUP_NAME = "SPLA Host"
DRS_RULE_NAME = "Windows VM run on SPLA Host"


# for logging
logger = logging.getLogger('spla_drs')
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s %(name)s %(levelname)-8s %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
# logger.addHandler(console_handler)


def check_and_set_drs_rule(host_address, login, passwd):
    vcenter_si = connect.SmartConnectNoSSL(host=host_address, user=login, pwd=passwd)

    content = vcenter_si.RetrieveContent()
    datacenter = content.rootFolder.childEntity[0]
    # datastores = datacenter.datastore
    vmfolder = datacenter.vmFolder
    raw_vmlist = vmfolder.childEntity

    cluster_list = datacenter.hostFolder.childEntity

    vmlist = get_all_vm_under_folder(raw_vmlist)

    for cluster in cluster_list:
        if not isinstance(cluster, vim.ClusterComputeResource):
            continue

        vm_windows_attribute_key = get_attribute_key_by_name(content, LICENSED_WINDOWS_FIELD_NAME)
        if vm_windows_attribute_key is None:
            logger.warn("Cluster {}, no VM have windows attribute.".format(cluster.name))
            continue

        host_spla_attribute_key = get_attribute_key_by_name(content, SPLA_LICENSED_HOST_FIELD_NAME)
        if host_spla_attribute_key is None:
            logger.warn("Cluster {}, no host have spla attribute.".format(cluster.name))
            continue

        vms_with_windows_attribute = [vm for vm in vmlist if len([tag for tag in vm.value if tag.key == vm_windows_attribute_key and tag.value == LICENSED_WINDOWS_FIELD_VALUE]) > 0 and get_cluster(vm.resourcePool) == cluster]
        hosts_with_spla_attribute = [host for host in cluster.host if len([tag for tag in host.value if tag.key == host_spla_attribute_key and tag.value == LICENSED_WINDOWS_FIELD_VALUE]) > 0]

        if len(vms_with_windows_attribute) < 1 or len(hosts_with_spla_attribute) < 1:
            logger.info("Cluster {}, no VM is windows licensed or no host have spla licensed. Nothing to process.".format(cluster.name))
            continue

        # create clusteer change container
        new_config = vim.cluster.ConfigSpecEx()
        vm_group_operation = vim.cluster.GroupSpec()
        host_group_operation = vim.cluster.GroupSpec()
        rule_operation = vim.cluster.RuleSpec()
        new_config.groupSpec.append(vm_group_operation)
        new_config.groupSpec.append(host_group_operation)

        vm_group_operation.operation = host_group_operation.operation = rule_operation.operation = "edit"

        # get VM and Host group
        vm_windows_group = None
        host_spla_group = None
        vm_host_rule = None
        for group in cluster.configurationEx.group:
            if isinstance(group, vim.cluster.VmGroup):
                if group.name == DRS_VM_GROUP_NAME:
                    vm_windows_group = group
                    continue
            elif isinstance(group, vim.cluster.HostGroup):
                if group.name == DRS_HOST_GROUP_NAME:
                    host_spla_group = group
                    continue

        # add Windows VMs to DRS windows VM group
        if vm_windows_group is None:
            logging.debug("Cluster {} don't have Windows VM group, need create.".format(cluster.name))
            vm_group_operation.operation = "add"
            vm_windows_group = vim.cluster.VmGroup()
            vm_windows_group.name = DRS_VM_GROUP_NAME
        logging.debug("Have {} Windows VMs for VM group on cluster {}.".format(len(vms_with_windows_attribute), cluster.name))
        vm_windows_group.vm = vms_with_windows_attribute
        vm_group_operation.info = vm_windows_group

        # add SPLA hosts to DRS SPLA host group
        if host_spla_group is None:
            logging.debug("Cluster {} don't have host SPLA group, need create.".format(cluster.name))
            host_group_operation.operation = "add"
            host_spla_group = vim.cluster.HostGroup()
            host_spla_group.name = DRS_HOST_GROUP_NAME
        logging.debug("Have {} SPLA hosts for host group on cluster {}.".format(len(hosts_with_spla_attribute), cluster.name))
        host_spla_group.host = hosts_with_spla_attribute
        host_group_operation.info = host_spla_group

        # Get existing VM-Host rule
        for rule in cluster.configurationEx.rule:
            if rule.name == DRS_RULE_NAME:
                vm_host_rule = rule
                break

        # Check VM-host rule, modify to standard if needed
        rule_need_modify = False
        if vm_host_rule is None:
            logging.debug("Cluster {} don't have Windows VM - SPLA host rule, need create.".format(cluster.name))
            rule_operation.operation = "add"
            vm_host_rule = vim.cluster.VmHostRuleInfo()
            rule_need_modify = True

        if vm_host_rule.name != DRS_RULE_NAME or vm_host_rule.vmGroupName != DRS_VM_GROUP_NAME or vm_host_rule.affineHostGroupName != DRS_HOST_GROUP_NAME or vm_host_rule.enabled is not True or vm_host_rule.mandatory is not True or vm_host_rule.userCreated is not True:
            rule_need_modify = True

        if rule_need_modify:
            logging.debug("Cluster {}'s' Windows VM - SPLA host rule, need modify to standard.".format(cluster.name))
            vm_host_rule.name = DRS_RULE_NAME
            vm_host_rule.vmGroupName = DRS_VM_GROUP_NAME
            vm_host_rule.affineHostGroupName = DRS_HOST_GROUP_NAME
            vm_host_rule.enabled = True
            vm_host_rule.mandatory = True
            vm_host_rule.userCreated = True
            rule_operation.info = vm_host_rule
            new_config.rulesSpec.append(rule_operation)

        # Submit change to cluster, and wait for finish
        task = cluster.ReconfigureComputeResource_Task(new_config, True)
        logging.info("Updating cluster {}.".format(cluster.name))
        while task.info.state == "running":
            time.sleep(0.5)
        logging.info("Cluster {} update finished, result is {}.".format(cluster.name, task.info.state))

    connect.Disconnect(vcenter_si)


if __name__ == "__main__":
    server_list = get_vsphere_config()
    for server in server_list:
        check_and_set_drs_rule(server.host, server.login, server.passwd)
