# TrollRestore With GUI!
**TrollRestore** is a versatile tool designed to install **TrollStore** on iOS/iPadOS versions 15.0 through 16.7 RC (20H18), and the latest iOS 17.0 (including the iOS 18.0 test version). It operates by replacing a system app of your choice with a custom **TrollHelper** binary, which you can then launch to proceed with the installation of TrollStore. TrollRestore leverages the backup and restore mechanism in iOS to inject the binary into the system app container, allowing for seamless integration.

For a comprehensive guide on installing TrollStore using TrollRestore, please refer to [this link](https://ios.cfw.guide/installing-trollstore-trollrestore).

## Usage
To use TrollRestore, clone the repository and execute the following commands:
```sh
pip install -r requirements.txt
python3 trollstore.py [system app]
```
If you're unsure which app to use as a target, it is recommended to use the **Tips** app, as shown below:
```
python3 trollstore.py Tips
```

## Post-installation
After using TrollRestore, note that it does not replace a proper persistence helper; it simply replaces the main binary of a system app with the embedded **TrollHelper**. For best results, after installing TrollStore, it is advisable to install a persistence helper (you can reuse the same app that was modified by TrollRestore). 

Due to the backup and restore method used by TrollRestore, the only way to revert your chosen app to its original state is to delete it and reinstall it from the App Store.

## iOS Version Support
As mentioned, this installer supports iOS/iPadOS versions from 15.0 up to 16.7 RC (20H18), as well as iOS 17.0.

Notably, all four versions of iOS 17.0 are supported:
- 21A326
- 21A327
- 21A329
- 21A331

While TrollRestore should theoretically support iOS 14, testing has revealed issues when restoring the backup to an iOS 14 device. Consequently, TrollStore installation on devices running iOS versions below 15 has been disabled for now.

## Computer Requirements
To use the precompiled builds, ensure your system meets the following requirements:

- **macOS**: A Mac running macOS 11 (Big Sur) or higher.
- **Windows**: A PC running Windows 10 or higher with iTunes installed.

## Need Help?
If you encounter any issues during the installation process, support is available on the [r/Jailbreak Discord server](https://discord.gg/jb).

## Credits
A big thank you to everyone who contributed to the development and improvement of TrollRestore:
* [JJTech](https://github.com/JJTech0130) - Creator of Sparserestore, the primary library used for restoring the TrollHelper binary.
* [Nathan](https://github.com/verygenericname) - For transforming Sparserestore into an installer for TrollStore.
* [Mike](https://github.com/TheMasterOfMike) and [Dhinak G](https://github.com/dhinakg) - For various enhancements to the installer.
* [doronz88](https://github.com/doronz88) - For developing `pymobiledevice3`, a crucial component of the installation process.
* [opa334](https://github.com/opa334) and [Alfie](https://github.com/alfiecg24) - For the creation and ongoing support of TrollStore.
* [Aaronp613](https://x.com/aaronp613) - For contributing minor improvements.
* [SeregonWar](https://github.com/seregonwar) - For creating the GUI and custom fork of the installer.
