# This script is called by distutils: note that some of the functions
# in here are only available when called by distutils.

import os, sys, shutil

def create_topographica_bat(python,location):
    # topographica.bat
    bat_path = os.path.join(location,'topographica.bat')
    f = open(bat_path,'w')
    f.write("@"+python+" "+location+r"\topographica %*")
    f.close()
    print "Created %s"%bat_path
    return bat_path


# CEBALERT: needs administrator permissions
def _create_association(python,scriptloc,ico_path):
    from _winreg import OpenKey,HKEY_CLASSES_ROOT,KEY_SET_VALUE,REG_SZ,SetValue

    bat_path = create_topographica_bat(python,scriptloc)

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

    # CEBALERT: sys.executable? And we do this in too many places (can't it be done once)?
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


    ### start menu:
    # ... examples shortcut
    start_menu_examples_shortcut = os.path.join(start_menu_folder,"Examples.lnk")
    create_shortcut(sys.prefix+r'\share\topographica\examples',
                    'Examples', start_menu_examples_shortcut, '')
    file_created(start_menu_examples_shortcut)

    # ... models shortcut
    start_menu_models_shortcut = os.path.join(start_menu_folder,"Models.lnk")
    create_shortcut(sys.prefix+r'\share\topographica\models',
                    'Models', start_menu_models_shortcut, '')
    file_created(start_menu_models_shortcut)


    file_created(_create_association(python,
                                     sys.prefix + r'\scripts',
                                     sys.prefix + r'\scripts\topographica.ico'))


def remove():
    pass



if len(sys.argv) > 1:
    # install and remove are for distutils
    if sys.argv[1] == '-install':
        install()
    elif sys.argv[1] == '-remove':
        remove()
    # create_batchfile is for svn/git users to get an executable batch file
    elif sys.argv[1] == 'create_batchfile':
        create_topographica_bat(sys.executable,os.getcwd())
    else:
        raise ValueError
