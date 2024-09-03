import platform
import sys
import traceback
from pathlib import Path
from tkinter import messagebox, filedialog, Tk, StringVar, BooleanVar, SUNKEN
import click
from packaging.version import parse as parse_version
from pymobiledevice3.cli.cli_common import Command
from pymobiledevice3.exceptions import NoDeviceConnectedError, PyMobileDevice3Exception
from pymobiledevice3.lockdown import create_using_usbmux, LockdownClient
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from sparserestore import backup, perform_restore, replace_app
import ttkbootstrap as ttk
from ttkbootstrap.constants import PRIMARY, SUCCESS, DANGER, INFO, WARNING, SECONDARY, LIGHT
import requests
import blessed
def exit(code=0):
    if platform.system() == "Windows" and getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        input("Press Enter to exit...")

    sys.exit(code)

def gui():
    root = ttk.Window(themename="darkly")
    root.title("TrollStore Manager")
    root.geometry("400x400")
    root.resizable(False, False)

    ttk.Label(root, text="App Name", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=10, sticky='w')
    app_name_var = StringVar()
    app_name_combobox = ttk.Combobox(root, textvariable=app_name_var, bootstyle=PRIMARY, font=("Helvetica", 12))
    app_name_combobox.grid(row=0, column=1, padx=10, pady=10, sticky='e')
    app_name_combobox['values'] = get_installed_apps()

    install_trollstore_var = BooleanVar(value=True)
    ttk.Checkbutton(root, text="Install TrollStore Helper", variable=install_trollstore_var, bootstyle=SUCCESS).grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='w')

    ttk.Button(root, text="Install", command=lambda: install_trollstore(app_name_var.get(), install_trollstore_var.get()), bootstyle=SUCCESS).grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    ttk.Button(root, text="Remove", command=lambda: remove_app(app_name_var.get()), bootstyle=DANGER).grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    ttk.Button(root, text="Backup", command=lambda: backup_app_data(app_name_var.get()), bootstyle=INFO).grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    ttk.Button(root, text="Restore", command=lambda: restore_app_data(app_name_var.get()), bootstyle=WARNING).grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    ttk.Button(root, text="View Logs", command=get_logs, bootstyle=SECONDARY).grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    status_var = StringVar()
    ttk.Label(root, textvariable=status_var, relief=SUNKEN, bootstyle=LIGHT).grid(row=7, column=0, columnspan=2, sticky='we', padx=10, pady=10)

    root.mainloop()

def get_installed_apps():
    try:
        service_provider = create_using_usbmux()
        apps_json = InstallationProxyService(service_provider).get_apps(application_type="User", calculate_sizes=False)
        app_names = [Path(value["Path"]).name for key, value in apps_json.items() if isinstance(value, dict) and "Path" in value]
        return app_names
    except Exception as e:
        messagebox.showerror("Error", f"Error getting apps: {str(e)}")
        return []

def install_trollstore(app_name, install_trollstore):
    try:
        if install_trollstore:
            process_app(app_name)
            messagebox.showinfo("Success", "TrollStore Helper installed.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def remove_app(app_name):
    try:
        backup.delete_app(app_name)
        messagebox.showinfo("Success", "App removed successfully.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def backup_app_data(app_name):
    try:
        backup_data = backup.Backup(
            files=[
                backup.Directory("", "AppDomain-" + app_name),
                backup.Directory("Documents", "AppDomain-" + app_name),
                backup.Directory("Library", "AppDomain-" + app_name),
                backup.Directory("tmp", "AppDomain-" + app_name),
            ]
        )
        backup.perform_backup(backup_data)
        messagebox.showinfo("Success", "Backup completed successfully.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def restore_app_data(app_name):
    try:
        restore_data = backup.Backup(
            files=[
                backup.Directory("", "AppDomain-" + app_name),
                backup.Directory("Documents", "AppDomain-" + app_name),
                backup.Directory("Library", "AppDomain-" + app_name),
                backup.Directory("tmp", "AppDomain-" + app_name),
            ]
        )
        perform_restore(restore_data)
        messagebox.showinfo("Success", "Restore completed successfully.")
        return "Restore completed successfully."
    except Exception as e:
        return f"Error during restore: {str(e)}"

def get_logs():
    try:
        logs = backup.fetch_logs()
        return logs
    except Exception as e:
        return f"Error getting logs: {str(e)}"

def process_app(app):
    service_provider = create_using_usbmux()
    os_names = {
        "iPhone": "iOS",
        "iPad": "iPadOS",
        "iPod": "iOS",
        "AppleTV": "tvOS",
        "Watch": "watchOS",
        "AudioAccessory": "HomePod Software Version",
        "RealityDevice": "visionOS",
    }

    device_class = service_provider.get_value(key="DeviceClass")
    device_build = service_provider.get_value(key="BuildVersion")
    device_version = parse_version(service_provider.product_version)

    if not all([device_class, device_build, device_version]):
        raise Exception("Failed to get device information! Make sure your device is connected and try again.")

    os_name = (os_names[device_class] + " ") if device_class in os_names else ""
    if (
        device_version < parse_version("15.0")
        or device_version > parse_version("18.0")
        or parse_version("16.7") < device_version < parse_version("17.0")
        or device_version == parse_version("16.7")
        and device_build != "20H18"
    ):
        raise Exception(f"{os_name}{device_version} ({device_build}) is not supported. This tool is only compatible with iOS/iPadOS 15.0 - 16.7 RC, 17.0, and 18.0.")

    apps_json = InstallationProxyService(service_provider).get_apps(application_type="User", calculate_sizes=False)

    app_path = None
    for key, value in apps_json.items():
        if isinstance(value, dict) and "Path" in value:
            potential_path = Path(value["Path"])
            if potential_path.name.lower() == app.lower():
                app_path = potential_path
                app = app_path.name

    if not app_path:
        click.secho(f"Failed to find the removable system app '{app}'!", fg="red")
        click.secho(f"Make sure you typed the app name correctly, and that the system app '{app}' is installed to your device.", fg="red")
        return
    elif Path("/private/var/containers/Bundle/Application") not in app_path.parents:
        click.secho(f"'{app}' is not a removable system app!", fg="red")
        click.secho("Please choose a removable system app. These will be Apple-made apps that can be deleted and re-downloaded.", fg="red")
        return

    app_uuid = app_path.parent.name

    try:
        response = requests.get("https://github.com/opa334/TrollStore/releases/latest/download/PersistenceHelper_Embedded")
        response.raise_for_status()
        helper_contents = response.content
    except Exception as e:
        click.secho(f"Failed to download TrollStore Helper: {e}", fg="red")
        return

    click.secho(f"Replacing {app} with TrollStore Helper. (UUID: {app_uuid})", fg="yellow")

    back = backup.Backup(
        files=[
            backup.Directory("", "RootDomain"),
            backup.Directory("Library", "RootDomain"),
            backup.Directory("Library/Preferences", "RootDomain"),
            backup.ConcreteFile("Library/Preferences/temp", "RootDomain", owner=33, group=33, contents=helper_contents, inode=0),
            backup.Directory(
                "",
                f"SysContainerDomain-../../../../../../../../var/backup/var/containers/Bundle/Application/{app_uuid}/{app}",
                owner=33,
                group=33,
            ),
            backup.ConcreteFile(
                "",
                f"SysContainerDomain-../../../../../../../../var/backup/var/containers/Bundle/Application/{app_uuid}/{app}/{app.split('.')[0]}",
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

@click.command(cls=Command)
@click.pass_context
def cli(ctx, service_provider: LockdownClient) -> None:
    gui()

def main():
    try:
        cli(standalone_mode=False)
    except NoDeviceConnectedError:
        click.secho("No device connected!", fg="red")
        click.secho("Please connect your device and try again.", fg="red")
        exit(1)
    except click.UsageError as e:
        click.secho(e.format_message(), fg="red")
        click.echo(cli.get_help(click.Context(cli)))
        exit(2)
    except Exception:
        click.secho("An error occurred!", fg="red")
        click.secho(traceback.format_exc(), fg="red")
        exit(1)

    exit(0)

if __name__ == "__main__":
    main()

