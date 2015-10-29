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

inputs = {'vcenter_ip': '15.10.10.11',
          'vcenter_password': 'Passw0rd',
          'vcenter_user': 'Administrator',
          'vm_name' : 'ubuntu12',
          'target_host': '15.10.10.12',
          'datacenter':'My_Datacenter',
          'template_name': 'Template-test'
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

def main():
    #args = GetArgs()
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
        # get the folder where VMs are kept for this datacenter
        vmFolder = datacenter.vmFolder        
        #vm_name = args.vm
        vm_name = inputs['vm_name']      
        vm = get_obj(content, [vim.VirtualMachine], vm_name)

        if vm.runtime.powerState != 'poweredOff':
            print "WARNING:: Power off your VM before creating template"
            sys.exit()

        target_host = get_obj(content, [vim.HostSystem], inputs['target_host'])

        relocate_spec = vim.vm.RelocateSpec()
        for datastore in target_host.datastore:
            #Store the OVS vApp VM in local datastore of each host
            if datastore.summary.type == 'VMFS':
                print "Storing the template in %s" % datastore.name
                relocate_spec.datastore = datastore
                break

        relocate_spec.host = target_host
        relocate_spec.pool = vm.resourcePool
                        
        cloneSpec = vim.vm.CloneSpec(powerOn=False, template=True, location=relocate_spec)
        print "Creating template... "
        task = vm.Clone(name=inputs['template_name'], folder=vmFolder, spec=cloneSpec)
        job_status = wait_for_task(task, si)
        if job_status:
            print "Template %s created successfully" % inputs['template_name']
    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        return 1
    except Exception, e:
        print "Caught exception: %s" % str(e)
        return 1
    
# Start program
if __name__ == "__main__":
    main()
