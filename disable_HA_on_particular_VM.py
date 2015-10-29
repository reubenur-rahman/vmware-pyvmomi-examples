'''
Copyright 2013-2014 Reubenur Rahman
All Rights Reserved
@author: reuben.13@gmail.com
'''

import atexit
import argparse
import sys
import time

from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect

inputs = {'vcenter_ip': '15.14.10.11',
          'vcenter_password': 'Passw0rd',
          'vcenter_user': 'Administrator',
          'vm_name' : 'ubuntu12',
          'cluster' : 'cluster2'   
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
    Wait and provide updates on a vSphere task
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


def main():
    try:
        si = None
        try:
            print "Trying to connect to VCENTER SERVER . . ."
            #si = connect.Connect(args.host, int(args.port), args.user, args.password, service="hostd")
            si = connect.Connect(inputs['vcenter_ip'], 443, inputs['vcenter_user'], inputs['vcenter_password'])
        except IOError, e:
            pass
            atexit.register(Disconnect, si)

        print "Connected to VCENTER SERVER %s " % inputs['vcenter_ip']

        content = si.RetrieveContent()

        vm = get_obj(content, [vim.VirtualMachine], inputs['vm_name'])

        cluster = get_obj(content, [vim.ClusterComputeResource], inputs['cluster'])
        settings = []
        cluster_spec = vim.cluster.ConfigSpec()
        config_spec = vim.cluster.DasVmConfigSpec()
        config_spec.operation = vim.option.ArrayUpdateSpec.Operation.edit
        config_info = vim.cluster.DasVmConfigInfo()
        config_info.key = vm
        config_info.restartPriority = vim.cluster.DasVmConfigInfo.Priority.disabled

        vm_settings = vim.cluster.DasVmSettings()
        #vm_settings.isolationResponse = vim.cluster.DasVmSettings.IsolationResponse.shutdown
        vm_settings.restartPriority = vim.cluster.DasVmSettings.RestartPriority.disabled
        monitor = vim.cluster.VmToolsMonitoringSettings()
        monitor.vmMonitoring = vim.cluster.DasConfigInfo.VmMonitoringState.vmMonitoringDisabled
        monitor.clusterSettings = False
        vm_settings.vmToolsMonitoringSettings = monitor

        config_info.dasSettings = vm_settings

        config_spec.info = config_info

        settings.append(config_spec)

        cluster_spec.dasVmConfigSpec = settings

        print "Disabling HA for VM ", vm.name
        task = cluster.ReconfigureCluster_Task(cluster_spec, True)
        wait_for_task(task, si)
        print "Successfully reconfigured HA priority"
    except vmodl.MethodFault, e:
            msg = e.msg
            if(msg.startswith("The setting of vmConfig is invalid")):
                print "Couldn't disable HA for %s" % vm.name
                print "Please turn off and turn on HA from Cluster settings."
            else:
                self.logger.error("Caught vmodl fault: %s" % e.msg)
                return 1
    except Exception, e:
        print "Caught exception: %s" % str(e)
        return 1
    
# Start program
if __name__ == "__main__":
    main()
