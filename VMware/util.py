import os
import logging

from pyVmomi import vim

SPLA_LICENSED_HOST_FIELD_NAME = "SPLA_LICENED_HOST"
LICENSED_WINDOWS_FIELD_NAME = "SPLA_LICENED_WINDOWS"
LICENSED_WINDOWS_FIELD_VALUE = "TRUE"

top_resource_pool_cache = {}


def find_top_resource_pool(resource):
    if not isinstance(resource, vim.ResourcePool):
        return None
    if resource in top_resource_pool_cache:
        return top_resource_pool_cache[resource]
    if resource.name == 'Resources':
        return 'ROOT'

    top_parent_name = find_top_resource_pool(resource.parent)

    if top_parent_name is 'ROOT':
        top_parent_name = resource.name

    top_resource_pool_cache[resource] = top_parent_name
    return top_parent_name


def get_all_vm_under_folder(vm_folder_child_entity):
    vm_list = []
    for item in vm_folder_child_entity:
        if isinstance(item, vim.VirtualMachine):
            vm_list.append(item)
        if isinstance(item, vim.Folder):
            # logger.debug('Found folder: {}, with {} child.'.format(item.name, len(item.childEntity)))
            child_list = (get_all_vm_under_folder(item.childEntity))
            if len(child_list) != 0:
                vm_list += child_list

    return vm_list


def get_cluster(vm_resource):
    if isinstance(vm_resource, vim.ResourcePool):
        return get_cluster(vm_resource.parent)
    elif isinstance(vm_resource, vim.ClusterComputeResource):
        return vm_resource
    return None


def get_attribute_key_by_name(content, name):
    attribute_key_list = [field.key for field in content.customFieldsManager.field if field.name == name]
    # Check if no any attribute
    if len(attribute_key_list) < 1:
        return None

    return attribute_key_list[0]


class Server(object):
    def __init__(self, name, host, login, passwd):
        self.name = name
        self.host = host
        self.login = login
        self.passwd = passwd
        self.result = None


def get_vsphere_config():
    config_str = None
    server_list = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_location = "vsphere_login.txt"
    try:
        with open(os.path.join(current_dir, config_file_location), "r") as config_file:
            config_str = config_file.readlines()
    except IOError:
        logging.error("Can't read config file {}, error message: {}".format(config_file_location, IOError.message))

    for line in config_str:
        if line.startswith("#"):
            logging.debug("Got commented config: {}".format(line))
            continue
            logging.debug("Got config: {}".format(line))
        config_element = line.strip().split(",")
        if len(config_element) != 4:
            logging.debug("Got in-complete config: {}. Will ignore.".format(line))
            continue
        config_element = [element.strip() for element in config_element]
        server = Server(*config_element)

        server_list.append(server)

    return server_list