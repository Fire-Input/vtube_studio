import websockets
import asyncio  # noqa: F401
import gradio as gr
import platform

# from modules import chat, shared
from extensions.vtube_studio import functions as vtube_studio_functions


params = {
    'activate': True,
    'host': None,
    'port': 8001,
    'model': 'mao_pro_en',
    'animation': 'Heart Success',
    'hotkeys': [],
}

websocket = None
models = []


async def get_os():
    if 'wsl2' and 'microsoft' in str(platform.uname()).lower():
        print('Running in WSL')
        host = f'{platform.uname().node}.local'
    else:
        print('Not running in WSL')
        host = platform.uname().node
    return host


async def connect():
    global websocket

    if websocket is not None:
        return websocket

    if params['host'] is not None:
        host = params['host']
    else:
        host = await get_os()

    # Connect to VTube Studio
    print('Connecting to VTube Studio...')
    try:
        websocket = await websockets.connect(f'ws://{host}:{params["port"]}', ping_interval=None)
    except asyncio.TimeoutError:
        print('Failed to connect to VTube Studio!  Please check the port number and make sure the API is running')
        return None
    if not websocket:
        print('Failed to connect to VTube Studio')
        return
    else:
        print('Connected to VTube Studio')

    # Get the authentication token
    print('Getting authentication token...')
    auth_token = await vtube_studio_functions.get_auth_token(websocket)

    # Authenticate the plugin with the authentication token
    print('Authenticating plugin...')
    auth_response = await vtube_studio_functions.authenticate(websocket, auth_token)

    # If authentication failed, exit
    if not auth_response:
        print('Plugin authentication failed')
        return
    else:
        print('Plugin authentication successful (VTube_Studio_API.py)')


async def play_animation():
    x = await vtube_studio_functions.execute_hotkey(websocket, params['animation'])
    return x


async def get_animations():
    global params
    hotkeys_list = await vtube_studio_functions.get_hotkeys(websocket)
    for hotkey in hotkeys_list:
        if len(hotkey) > 0 and hotkey['name'] not in params['hotkeys']:
            params['hotkeys'].append(hotkey['name'])
    print(params['hotkeys'])
    return gr.update(choices=params['hotkeys'], value=params['animation'], label='Animation')


def ui():
    global params
    # Gradio elements
    with gr.Accordion("VTube Studio"):
        with gr.Row():
            activate = gr.Checkbox(value=params['activate'], label='Activate VTube Studio')
            port_number = gr.Number(value=params['port'], label='Port', precision=0)
            connect_button = gr.Button('Connect')

        model_dropdown = gr.Dropdown(choices=models, value=params['model'], label='Model')

        with gr.Row():
            hotkey_dropdown = gr.Dropdown(choices=params['hotkeys'], value=params['animation'], label='Animation')
            animation_button = gr.Button('Play Animation')
            refresh_button = gr.Button('Refresh')

    # Event functions to update the parameters in the backend
    activate.change(lambda x: params.update({'activate': x}), activate, None)
    model_dropdown.change(lambda x: params.update({'model': x}), model_dropdown, None)
    port_number.change(lambda x: params.update({'port': x}), port_number, None)
    hotkey_dropdown.change(lambda x: get_animations(), hotkey_dropdown, None)

    # Connect to VTube Studio
    connect_button.click(fn=connect)

    # Play animation
    animation_button.click(fn=play_animation)

    # Refresh hotkeys
    refresh_button.click(fn=get_animations)
