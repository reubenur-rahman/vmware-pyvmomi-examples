'''
Copyright 2014-2015 Reubenur Rahman
All Rights Reserved
@author: reuben.13@gmail.com
'''

import atexit
import sys
import time

from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect

inputs = {'vcenter_ip': '15.22.18.10',
          'vcenter_password': 'Passw0rd123',
          'vcenter_user': 'Administrator',
          'datacenter' : 'Datacenter',
          'cluster': 'ReubenCluster',
          'dvs_name': 'TestDVS1',
          'dv_port_name': 'TestDVPortGroup1'
          }

def get_obj(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """    
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def wait_for_task(task, actionName='job', hideResult=False):
    """
    Waits and provides updates on a vSphere task
    """
    
    while task.info.state == vim.TaskInfo.State.running:
        time.sleep(2)
    
    if task.info.state == vim.TaskInfo.State.success:
        if task.info.result is not None and not hideResult:
            out = '%s completed successfully, result: %s' % (actionName, task.info.result)
            print out
        else:
            out = '%s completed successfully.' % actionName
            print out
    else:
        out = '%s did not complete successfully: %s' % (actionName, task.info.error)
        raise task.info.error
        print out
    
    return task.info.result

def add_dvPort_group(si, dv_switch):
    dv_pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
    dv_pg_spec.name = inputs['dv_port_name']
    dv_pg_spec.numPorts = 32
    dv_pg_spec.type = vim.dvs.DistributedVirtualPortgroup.PortgroupType.earlyBinding

    dv_pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
    dv_pg_spec.defaultPortConfig.securityPolicy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()

    dv_pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec()
    dv_pg_spec.defaultPortConfig.vlan.vlanId = [vim.NumericRange(start=1, end=4094)]
    dv_pg_spec.defaultPortConfig.securityPolicy.allowPromiscuous = vim.BoolPolicy(value=True)
    dv_pg_spec.defaultPortConfig.securityPolicy.forgedTransmits = vim.BoolPolicy(value=True)        

    dv_pg_spec.defaultPortConfig.vlan.inherited = False
    dv_pg_spec.defaultPortConfig.securityPolicy.macChanges = vim.BoolPolicy(value=False)
    dv_pg_spec.defaultPortConfig.securityPolicy.inherited = False

    task = dv_switch.AddDVPortgroup_Task([dv_pg_spec])
    wait_for_task(task, si)
    print "Successfully created DV Port Group ", inputs['dv_port_name']

def create_dvSwitch(si, content, network_folder, cluster):
    pnic_specs = []
    dvs_host_configs = []
    uplink_port_names = []
    dvs_create_spec = vim.DistributedVirtualSwitch.CreateSpec()
    dvs_config_spec = vim.DistributedVirtualSwitch.ConfigSpec()
    dvs_config_spec.name = inputs['dvs_name']
    dvs_config_spec.uplinkPortPolicy = vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy()
    hosts = cluster.host
    for x in range(len(hosts)):
        uplink_port_names.append("dvUplink%d" % x)

    for host in hosts:
        dvs_config_spec.uplinkPortPolicy.uplinkPortName = uplink_port_names
        dvs_config_spec.maxPorts = 2000
        pnic_spec = vim.dvs.HostMember.PnicSpec()
        pnic_spec.pnicDevice = 'vmnic1'
        pnic_specs.append(pnic_spec)
        dvs_host_config = vim.dvs.HostMember.ConfigSpec()
        dvs_host_config.operation = vim.ConfigSpecOperation.add
        dvs_host_config.host = host
        dvs_host_configs.append(dvs_host_config)
        dvs_host_config.backing = vim.dvs.HostMember.PnicBacking()
        dvs_host_config.backing.pnicSpec = pnic_specs
        dvs_config_spec.host = dvs_host_configs

    dvs_create_spec.configSpec = dvs_config_spec
    dvs_create_spec.productInfo = vim.dvs.ProductSpec(version='5.1.0')

    task = network_folder.CreateDVS_Task(dvs_create_spec)
    wait_for_task(task, si)
    print "Successfully created DVS ", inputs['dvs_name']
    return get_obj(content, [vim.DistributedVirtualSwitch], inputs['dvs_name'])
	
def main():
    try:
        si = None
        try:
            print "Trying to connect to VCENTER SERVER . . ."
            si = connect.Connect(inputs['vcenter_ip'], 443, inputs['vcenter_user'], inputs['vcenter_password'])
        except IOError, e:
            pass
            atexit.register(Disconnect, si)

        print "Connected to VCENTER SERVER !"
        
        content = si.RetrieveContent()
        datacenter = get_obj(content, [vim.Datacenter], inputs['datacenter'])
	cluster = get_obj(content, [vim.ClusterComputeResource], inputs['cluster'])
	network_folder = datacenter.networkFolder
	#Create DV Switch
	dv_switch = create_dvSwitch(si, content, network_folder, cluster)
	#Add port group to this switch
	add_dvPort_group(si, dv_switch)

    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        return 1
    except Exception, e:
        print "Caught exception: %s" % str(e)
        return 1
    
# Start program
if __name__ == "__main__":
    main()
