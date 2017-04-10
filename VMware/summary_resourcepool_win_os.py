import datetime
import logging
import os
import smtplib
import sys
from collections import defaultdict, namedtuple
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import xlsxwriter
from concurrent import futures
from pyVim import connect
from pyVmomi import vim

from util import find_top_resource_pool, get_all_vm_under_folder, get_attribute_key_by_name, \
    LICENSED_WINDOWS_FIELD_NAME, LICENSED_WINDOWS_FIELD_VALUE, get_vsphere_config

# for email
MAIL_TO = ["receiver01@example.com", "receiver02@example.com"]
MAIL_FROM = "report@example.com"
SMTP_HOST = "smtp.example.com"


logger = logging.getLogger('os_counter')
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s %(name)s %(levelname)-8s %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# Excel column setting
XLSX_COL_RESOURCE_POOL = 0
XLSX_COL_VM_NAME = 1
XLSX_COL_VM_CPU = 2
XLSX_COL_VM_RAM = 3
XLSX_COL_VM_OS = 4
XLSX_COL_VM_POWERED_ON = 5
XLSX_COL_VM_WINDOWS_LICENSED = 6
XLSX_COL_VM_IMMEDIATE_RESOURCE_POOL = 7
XLSX_COL_VM_CPU_USAGE = 8
XLSX_COL_VM_RAM_USAGE = 9


ResourceData = namedtuple("ResourceData", "type min max avg")


class VM(object):
    def __init__(self):
        self.name = None
        self.resource_pool_name = None
        self.top_resource_pool_name = None
        self.config_cpu = 0
        self.config_ram = 0
        self.cpu_usage = 0
        self.ram_usage = 0
        self.os = None
        self.powered_on = False
        self.windows_licensed = False


def get_vm_resource_usage(perf_manager, vm):
    # startTime = datetime.datetime.now() - datetime.timedelta(days=1)
    start_time = datetime.datetime.now() - datetime.timedelta(hours=1)
    end_time = datetime.datetime.now()

    """ 6 is cpu.usagemhz.average, found by perfManager.perfCounter. [i for i in perfManager.perfCounter if i.key == 6],
     [i for i in perfManager.perfCounter if i.groupInfo.key == "mem" and i.nameInfo.key == "consumed" and i.rollupType == "average"]
    https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.PerformanceManager.html
    """
    # Query CPU
    metric_id = vim.PerformanceManager.MetricId(counterId=6, instance="*")
    query = vim.PerformanceManager.QuerySpec(maxSample=1,
                                             entity=vm,
                                             metricId=[metric_id],
                                             startTime=start_time,
                                             endTime=end_time)
    cpu_data = perf_manager.QueryPerf(querySpec=[query])
    if len(cpu_data) > 0 and len(cpu_data[0].value) > 0:
        raw_cpu_data = cpu_data[0].value[0].value
    else:
        raw_cpu_data = [0]

    # Query RAM
    metric_id = vim.PerformanceManager.MetricId(counterId=98, instance="*")
    query = vim.PerformanceManager.QuerySpec(maxSample=1,
                                             entity=vm,
                                             metricId=[metric_id],
                                             startTime=start_time,
                                             endTime=end_time)
    mem_data = perf_manager.QueryPerf(querySpec=[query])
    if len(mem_data) > 0 and len(mem_data[0].value) > 0:
        raw_mem_data = mem_data[0].value[0].value
    else:
        raw_mem_data = [0]

    cpu = ResourceData("CPU", min(raw_cpu_data), max(raw_cpu_data), sum(raw_cpu_data)/len(raw_cpu_data))
    mem = ResourceData("Memory", min(raw_mem_data), max(raw_mem_data), sum(raw_mem_data)/len(raw_mem_data))

    return cpu, mem


def get_windows_under_gid(host, login, passwd):
    vcenter_si = None
    try:
        vcenter_si = connect.SmartConnectNoSSL(host=host, user=login, pwd=passwd)
    except:
        logger.error("Can't login to {}".format(host))
        return None
    content = vcenter_si.RetrieveContent()
    datacenter = content.rootFolder.childEntity[0]
    # datastores = datacenter.datastore
    vmfolder = datacenter.vmFolder
    raw_vmlist = vmfolder.childEntity
    perf_manager = content.perfManager
    # cluster = datacenter.hostFolder.childEntity[0]
    vmlist = get_all_vm_under_folder(raw_vmlist)
    vm_windows_attribute_key = get_attribute_key_by_name(content, LICENSED_WINDOWS_FIELD_NAME)

    gid_windows_count = defaultdict(list)
    # os_set = set()
    # for vm in vmlist:
    #     os_set.add(vm.config.guestId)
    for vm in vmlist:
        # resourcePool is None means this it template
        if vm.resourcePool is None:
            continue
        top_parent_name = find_top_resource_pool(vm.resourcePool)
        vm_data = VM()
        vm_data.name = vm.name
        vm_data.resource_pool_name = vm.resourcePool.name
        vm_data.top_resource_pool_name = top_parent_name
        vm_data.config_cpu = vm.summary.config.numCpu
        vm_data.config_ram = vm.summary.config.memorySizeMB
        vm_data.os = vm.config.guestId
        vm_data.powered_on = vm.summary.runtime.powerState == "poweredOn"
        if vm_data.powered_on:  # and vm_data.os.startswith("win"):
            cpu_usage, mem_usage = get_vm_resource_usage(perf_manager, vm)
            vm_data.cpu_usage = cpu_usage.avg
            vm_data.ram_usage = mem_usage.avg
        if vm_windows_attribute_key is not None:
            for tag in vm.value:
                if tag.key == vm_windows_attribute_key and tag.value == LICENSED_WINDOWS_FIELD_VALUE:
                    vm_data.windows_licensed = True

        gid_windows_count[top_parent_name].append(vm_data)
        # if vm.config.guestId.startswith('win'):
            # top_parent_name = find_top_resource_pool(vm.resourcePool)
            # if top_parent_name is not None and top_parent_name.startswith('GID'):
            # if top_parent_name is not None and 'GID' in top_parent_name:
                # gid_windows_count[top_parent_name] += 1

    # total_gid_windows_count = 0
    # for k, v in sorted(gid_windows_count.items()):
    #     logger.debug("{} have {} windows.".format(k, v))
    #     total_gid_windows_count += v
    # logger.info('Total: {}'.format(total_gid_windows_count))
    connect.Disconnect(vcenter_si)
    return {"host": host, "gid_windows_count": gid_windows_count}


def write_server_worksheet_header(worksheet):
    worksheet.write(0, XLSX_COL_RESOURCE_POOL, "Resource Pool Name")
    worksheet.write(0, XLSX_COL_VM_NAME, "VM Name")
    worksheet.write(0, XLSX_COL_VM_OS, "OS")
    worksheet.write(0, XLSX_COL_VM_POWERED_ON, "Powered On")
    worksheet.write(0, XLSX_COL_VM_WINDOWS_LICENSED, "Windows Licensed")
    worksheet.write(0, XLSX_COL_VM_IMMEDIATE_RESOURCE_POOL, "Immediate Resource Pool")
    worksheet.write(0, XLSX_COL_VM_CPU, "Number of vCPU")
    worksheet.write(0, XLSX_COL_VM_RAM, "Memory (MB)")
    worksheet.write(0, XLSX_COL_VM_CPU_USAGE, "CPU Usage (MHz)")
    worksheet.write(0, XLSX_COL_VM_RAM_USAGE, "Memory Usage (KB)")


def write_data_to_excel(output_xlsx_filename, server_list):
    with xlsxwriter.Workbook(output_xlsx_filename) as workbook:
        for server in server_list:
            # if got error on collect server data, will cause result is None
            if server.result is None:
                continue
            server_ws = workbook.add_worksheet(server.name)
            write_server_worksheet_header(server_ws)
            row_count = 1
            gid_sorted_server_items = sorted(server.result.items())
            for resource_pool, vm_list in gid_sorted_server_items:
                for vm in vm_list:
                    server_ws.write(row_count, XLSX_COL_RESOURCE_POOL, resource_pool)
                    server_ws.write(row_count, XLSX_COL_VM_NAME, vm.name)
                    server_ws.write(row_count, XLSX_COL_VM_OS, vm.os)
                    server_ws.write(row_count, XLSX_COL_VM_POWERED_ON, vm.powered_on)
                    server_ws.write(row_count, XLSX_COL_VM_WINDOWS_LICENSED, vm.windows_licensed)
                    server_ws.write(row_count, XLSX_COL_VM_IMMEDIATE_RESOURCE_POOL, vm.resource_pool_name)
                    server_ws.write(row_count, XLSX_COL_VM_CPU, vm.config_cpu)
                    server_ws.write(row_count, XLSX_COL_VM_RAM, vm.config_ram)
                    server_ws.write(row_count, XLSX_COL_VM_CPU_USAGE, vm.cpu_usage)
                    server_ws.write(row_count, XLSX_COL_VM_RAM_USAGE, vm.ram_usage)
                    row_count += 1

            server_ws.autofilter(0, 0, row_count - 1, 9)
            server_ws.filter_column(XLSX_COL_RESOURCE_POOL, "pool == GID*")
            server_ws.filter_column(XLSX_COL_VM_OS, "os == win*")
            server_ws.filter_column(XLSX_COL_VM_POWERED_ON, "powered_on == TRUE")

            # row_count = 1
            # for resource_pool, vm_list in gid_sorted_server_items:
            #     for vm in vm_list:
            #         if resource_pool.startswith("GID") and vm.os.startswith("win") and vm.powered_on == "TRUE":
            #             server_ws.set_row(row_count, options={'hidden': True})
            #         row_count += 1


def send_mail(message, report_date, attachment_file_path = None):
    mail = MIMEMultipart()
    mail["Subject"]="SCC Windows VM report - {}".format(report_date)
    mail["To"] = ",".join(MAIL_TO)
    mail["From"] = MAIL_FROM
    mail_body = MIMEText(message, "plain")
    mail.attach(mail_body)

    if attachment_file_path is not None and os.path.isfile(attachment_file_path):
        attachment = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with open(attachment_file_path, "rb") as reader:
            attachment.set_payload(reader.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_file_path))
        mail.attach(attachment)

    smtp = smtplib.SMTP(SMTP_HOST, 25)
    try:
        smtp.ehlo()
        #smtp.starttls()
        #smtp.ehlo()
        #smtp.login(MAIL_FROM, MAIL_PASSWD);
        smtp.sendmail(MAIL_FROM,MAIL_TO,mail.as_string())
        smtp.quit()
    except:
        logger.error("Can't send mail...")


if __name__ == "__main__":
    report_datetime = datetime.datetime.now().strftime("%Y%m%d-%H_%M_%S")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    report_store_dir = os.path.join(current_dir, "reports")
    if not os.path.isdir(report_store_dir) or not os.access(report_store_dir, os.W_OK):
        logger.error("Can't write to {}".format(report_store_dir))
        sys.exit(1)
    excel_report_path = os.path.join(report_store_dir, "vm_os_information - {}.xlsx".format(report_datetime))

    server_list = get_vsphere_config()
    usage = []
    with futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = []
        for server in server_list:
            results.append(executor.submit(get_windows_under_gid, server.host, server.login, server.passwd))
        for result in results:
            if result.result() is None:
                continue
            for server in server_list:
                if server.host == result.result()["host"]:
                    server.result = result.result()["gid_windows_count"]
                    break

    write_data_to_excel(excel_report_path, server_list)
    send_mail("", report_datetime, excel_report_path)
