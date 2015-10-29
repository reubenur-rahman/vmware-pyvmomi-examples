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

inputs = {'vcenter_ip': '15.22.10.11',
          'vcenter_password': 'Password123',
          'vcenter_user': 'Administrator',
          'vm_name': 'ubuntu12',
          'destination_host': '15.22.11.9'
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

    try:
        si = None
        try:
            print "Trying to connect to VCENTER SERVER . . ."
            si = connect.Connect(inputs['vcenter_ip'], 443, inputs['vcenter_user'], inputs['vcenter_password'], service="hostd")
        except IOError, e:
            pass
            atexit.register(Disconnect, si)

        print "Connected to VCENTER SERVER !"

        content = si.RetrieveContent()

        vm = get_obj(content, [vim.VirtualMachine], inputs['vm_name'])
        destination_host = get_obj(content, [vim.HostSystem], inputs['destination_host'])

        resource_pool = vm.resourcePool

        if vm.runtime.powerState != 'poweredOn':
            print "WARNING:: Migration is only for Powered On VMs"
            sys.exit()

        migrate_priority = vim.VirtualMachine.MovePriority.defaultPriority

        msg = "Migrating %s to destination host %s" % (inputs['vm_name'], inputs['destination_host'])
        print msg

        #Live Migration :: Change host only
        task = vm.Migrate(pool=resource_pool, host=destination_host, priority=migrate_priority)

#         Live Migration :: Change both host and datastore
#         vm_relocate_spec = vim.vm.RelocateSpec()
#         vm_relocate_spec.host = destination_host
#         vm_relocate_spec.pool = resource_pool
#         datastores = destination_host.datastore
#         Assuming Migrating between local datastores
#         for datastore in datastores:
#             if datastore.summary.type == 'VMFS':
#                 vm_relocate_spec.datastore = datastore
#                 break
#
#         task = vm.Relocate(spec=vm_relocate_spec)

        # Wait for Migrate to complete
        wait_for_task(task, si)

    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        return 1
    except Exception, e:
        print "Caught exception: %s" % str(e)
        return 1

# Start program
if __name__ == "__main__":
    main()
