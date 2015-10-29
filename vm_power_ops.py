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
from pyVim.connect import Disconnect, SmartConnect, GetSi

inputs = {'vcenter_ip': '10.10.10.211',
          'vcenter_password': 'Password123',
          'vcenter_user': 'Administrator',
          'vm_name' : 'reuben-test',
          #Start, Stop(force), Suspend(force)
          'operation' : 'suspend',
          'force' : True,   
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

def wait_for_task(task, raiseOnError=True, si=None, pc=None):
    if si is None:
        si = GetSi()

    if pc is None:
        sc = si.RetrieveContent()
        pc = sc.propertyCollector

    # First create the object specification as the task object.
    objspec = vmodl.Query.PropertyCollector.ObjectSpec()
    objspec.SetObj(task)

    # Next, create the property specification as the state.
    propspec = vmodl.Query.PropertyCollector.PropertySpec()
    propspec.SetType(vim.Task);
    propspec.SetPathSet(["info.state"]);
    propspec.SetAll(True)

    # Create a filter spec with the specified object and property spec.
    filterspec = vmodl.Query.PropertyCollector.FilterSpec()
    filterspec.SetObjectSet([objspec])
    filterspec.SetPropSet([propspec])

    # Create the filter
    filter = pc.CreateFilter(filterspec, True)
   
    # Loop looking for updates till the state moves to a completed state.
    taskName = task.GetInfo().GetName()
    update = pc.WaitForUpdates(None)
    state = task.GetInfo().GetState()
    while state != vim.TaskInfo.State.success and \
            state != vim.TaskInfo.State.error:
        if (state == 'running') and (taskName.info.name != "Destroy"):
            # check to see if VM needs to ask a question, thow exception
            vm = task.GetInfo().GetEntity()
            if vm is not None and isinstance(vm, vim.VirtualMachine):
                qst = vm.GetRuntime().GetQuestion()
            if qst is not None:
                raise Exception("Task blocked, User Intervention required")
      
    update = pc.WaitForUpdates(update.GetVersion())
    state = task.GetInfo().GetState()
         
    filter.Destroy()
    if state == "error" and raiseOnError:
        raise task.GetInfo().GetError()
      
    return state


def invoke_and_track(func, *args, **kw):
    try :
        task = func(*args, **kw)
        wait_for_task(task)
    except:
        raise


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

        if inputs['operation'] == 'stop' or inputs['operation'] == 'suspend':
            force = inputs['force']
   
        vm = get_obj(content, [vim.VirtualMachine], inputs['vm_name'])

        #current_state = vm.runtime.powerState
        
        if inputs['operation'] == 'start':
            invoke_and_track(vm.PowerOn, None)

        elif inputs['operation'] == 'stop':
            if not force:
                invoke_and_track(vm.ShutdownGuest)
            else:
                invoke_and_track(vm. PowerOff)
        
        elif inputs['operation'] == 'suspend':
            if not force:
                invoke_and_track(vm.StandbyGuest)
            else:
                invoke_and_track(vm. Suspend)
                
        #wait_for_task(task, si)        
        
    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        return 1
    except Exception, e:
        if str(e) == 'Query':
            return 1
        print "Caught exception: %s" % str(e)
        return 1
    
# Start program
if __name__ == "__main__":
    main()
