# Oobabooga's Text Generation WebUI extension for VTube Studio

This repository contains an extension for [Oobabooga's Text Generation WebUI](https://github.com/oobabooga/Text-Generation-Web-UI) that integrates with VTube Studio.

## Getting started

### Prerequisites

This extension requires the following packages to be installed:

- `websockets`

### Installation

1. Clone this repo `git clone https://github.com/Fire-Input/vtube_studio` to the `extensions` folder in the WebUI.
2. Install the requirements with `pip install -r requirements.txt`
3. Enable the VTube Studio API in VTube Studio's settings.
4. Launch the WebUI.

### Usage

1. Start the Text Generation WebUI and enable the VTube Studio extension.
2. Enter the port number, and optionally the host of the VTube Studio's API.
3. Click the connect button to connect to VTube Studio.
4. Allow the extension from the popup on VTube Studio.
5. Choose the model, animation, and expression from the dropdown menus.

## Issues
1. If you are running the WebUI with WSL and VTube Studio on Windows, then you should either leave the host blank or you can enter the ip/hostname that WSL uses to point to your Windows device.
2. If using WSL, you may need to allow WSL through your local firewall, you can use this PowerShell command on Windows: `New-NetFirewallRule -DisplayName "WSL" -Direction Inbound  -InterfaceAlias "vEthernet (WSL)"  -Action Allow`

## Miscellaneous Info and Future Plans
This extension is currently a work in progress and may be subject to bugs and other issues. Here are some future plans for the extension:

- Add support for controlling items in VTube Studio.
- Improve error handling and error messages
- Allow for better configuration of the extension
- Add more features for controlling VTube Studio, such as model movement and physics.
- Implement a feature to detect the emotion of generated text and play a corresponding hotkey for more realistic expressions.
- Investigate the possibility of syncing mouth movements with TTS.
- Implement random values for certain parameters like speed or position to add variety to animations.

If you encounter any issues while using this extension, please create a GitHub issue.

Please feel free to suggest any further improvements or features that you would like to see in this extension.