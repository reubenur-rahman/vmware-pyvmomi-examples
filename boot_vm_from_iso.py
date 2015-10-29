'''
Copyright 2014-2015 Reubenur Rahman
All Rights Reserved
@author: reuben.13@gmail.com
'''

import atexit
import time

from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect

inputs = {'vcenter_ip': '15.21.18.11',
          'vcenter_password': 'Password123',
          'vcenter_user': 'Administrator',
          'vm_name': 'reuben-aur',
          'datastor_iso_path': '[datastore-9] ubuntu12.iso'
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
            si = connect.Connect(inputs['vcenter_ip'], 443, inputs['vcenter_user'], inputs['vcenter_password'], version = "vim.version.version8")
        except IOError, e:
            pass
            atexit.register(Disconnect, si)

        print "Connected to VCENTER SERVER !"

        content = si.RetrieveContent()

        vm_name = inputs['vm_name']
        vm = get_obj(content, [vim.VirtualMachine], vm_name)

        print "Attaching iso to CD drive of ", vm_name
        cdspec = None
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualCdrom):
                cdspec = vim.vm.device.VirtualDeviceSpec()
                cdspec.device = device
                cdspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit

                cdspec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
                for datastore in vm.datastore:
                    cdspec.device.backing.datastore = datastore
                    break
                cdspec.device.backing.fileName = inputs['datastor_iso_path']
                cdspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
                cdspec.device.connectable.startConnected = True
                cdspec.device.connectable.allowGuestControl = True

        vmconf = vim.vm.ConfigSpec()
        vmconf.deviceChange = [cdspec]
        print "Giving first priority for CDrom Device in boot order"
        vmconf.bootOptions = vim.vm.BootOptions(bootOrder=[vim.vm.BootOptions.BootableCdromDevice()])

        task = vm.ReconfigVM_Task(vmconf)

        wait_for_task(task, si)

        print "Successfully changed boot order priority and attached iso to the CD drive of VM ", vm_name

        print "Power On the VM to boot from iso"
        vm. PowerOnVM_Task()

    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        return 1
    except Exception, e:
        print "Caught exception: %s" % str(e)
        return 1

# Start program
if __name__ == "__main__":
    main()
