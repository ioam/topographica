#!python

import os, sys, shutil
from _winreg import OpenKey,HKEY_CLASSES_ROOT,KEY_SET_VALUE,REG_SZ,SetValue

def _create_association(python,scriptloc,ico_path):

    # topographica.bat
    bat_path = os.path.join(scriptloc,'topographica.bat')
    f = open(bat_path,'w')
    f.write("@"+python+" "+scriptloc+r"\topographica %*")
    f.close()

    # Link '.ty' file extension to  "topographica.bat -g"
    os.system('assoc .ty=Topographica.Script')
    os.system('ftype Topographica.Script="' + bat_path + '" -g "%1"')
    
    # and add the Topographica icon to the registry.
    namepathkey = OpenKey(HKEY_CLASSES_ROOT,'Topographica.Script',0,KEY_SET_VALUE)
    SetValue(namepathkey,None,REG_SZ,'Topographica Script')
    SetValue(namepathkey,'DefaultIcon',REG_SZ, ico_path)
    # CEBALERT: needs to be removed on remove()

    return bat_path


def install():

    python = sys.prefix + r'\python.exe'

    start_menu_folder = get_special_folder_path('CSIDL_COMMON_PROGRAMS') + r'\Topographica'

    if not os.path.isdir(start_menu_folder):
        os.mkdir(start_menu_folder)
        directory_created(start_menu_folder)

    topographica_shortcut_name = 'Topographica.lnk'


    ### start menu: topographica shortcut
    start_menu_topographica_shortcut = os.path.join(start_menu_folder,
                                                    topographica_shortcut_name)
    args = sys.prefix + r'\scripts\topographica -g'

    create_shortcut(python, 'Topographica', start_menu_topographica_shortcut, 
                    args, '', sys.prefix + r'\scripts\topographica.ico')
    file_created(start_menu_topographica_shortcut)


    ### desktop: topographica shortcut
    desktop_folder = get_special_folder_path("CSIDL_DESKTOPDIRECTORY")

    shutil.copy(start_menu_topographica_shortcut,
                os.path.join(desktop_folder,topographica_shortcut_name))

    file_created(os.path.join(desktop_folder, topographica_shortcut_name))


    ### start menu: examples shortcut
    start_menu_examples_shortcut = os.path.join(start_menu_folder,"Examples.lnk")
    create_shortcut(sys.prefix+r'\share\topographica\examples', 
                    'Examples', start_menu_examples_shortcut, '')
    file_created(start_menu_examples_shortcut)


    file_created(_create_association(python,
                                     sys.prefix + r'\scripts',
                                     sys.prefix + r'\scripts\topographica.ico'))
                       
   
def remove():
    pass



if len(sys.argv) > 1:
    if sys.argv[1] == '-install':
        install()
    elif sys.argv[1] == '-remove':
        remove()
    else:
        raise ValueError
