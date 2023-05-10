import websockets
import asyncio  # noqa: F401
import gradio as gr
import platform

from extensions.vtube_studio import functions as vtube_studio_functions


params = {
    'activate': True,
    'host': "",
    'port': 8001,
    'model': None,
    'model_dict': {},
    'animation': None,
    'animation_list': [],
    'expression': None,
    'expression_list': [],
}

websocket = None


async def get_os():
    if 'wsl2' and 'microsoft' in str(platform.uname()).lower():
        print('Running in WSL, using hostname.local because WSL uses a virtual network')
        host = f'{platform.uname().node}.local'
    else:
        # print('Not running in WSL')
        host = platform.uname().node
    return host


async def connect():
    global websocket, params

    if not params['activate']:
        return

    if not params['host']:
        params.update({'host': await get_os()})

    # Connect to VTube Studio
    print('Connecting to VTube Studio...')
    try:
        websocket = await websockets.connect(f'ws://{params["host"]}:{params["port"]}', ping_interval=None)
    except asyncio.TimeoutError as err:
        raise asyncio.TimeoutError('Failed to connect to VTube Studio!  Please check the port number and make sure the API is running') from err
    if not websocket:
        raise Exception('Failed to connect to VTube Studio!')
    else:
        print('Connected to VTube Studio')

    # Get the authentication token
    # print('Getting authentication token...')
    auth_token = await vtube_studio_functions.get_auth_token(websocket)

    # Authenticate the plugin with the authentication token
    # print('Authenticating plugin...')
    auth_response = await vtube_studio_functions.authenticate(websocket, auth_token)

    # If authentication failed, exit
    if not auth_response:
        raise Exception('Plugin authentication failed!')
    else:
        # print('Plugin authentication successful (VTube_Studio_API.py)')
        pass


async def disconnect(x):
    global websocket

    if not x:
        if websocket:
            print('Disconnecting from VTube Studio...')
            try:
                await websocket.close()
            except Exception as err:
                print(err)
                websocket = None
            print('Disconnected from VTube Studio')
            websocket = None


async def update_menus():
    model_list = await get_models()

    hotkey_list = await get_available_hotkeys()

    return *model_list, *hotkey_list


# play the hotkey in VTube Studio
async def play_hotkey(hotkey):
    result = await vtube_studio_functions.execute_hotkey(websocket, hotkey)
    return result


#  get the list of available animations and expressions from VTube Studio
async def get_available_hotkeys(model_id=None):
    global params
    animation_list, expression_list = await vtube_studio_functions.get_hotkeys(websocket, model_id=model_id)
    params.update({'animation_list': animation_list})
    # print(f"Animations: {params['animation_list']}")
    if params['animation_list']:
        params.update({'animation': params['animation_list'][0]})  # explicitly update the params dictionary
    else:
        params.update({'animation': None})

    params.update({'expression_list': expression_list})
    # print(f"Expressions: {params['expression_list']}")
    if params['expression_list']:
        params.update({'expression': params['expression_list'][0]})  # explicitly update the params dictionary
    else:
        params.update({'expression': None})

    return [gr.update(choices=animation_list, value=params['animation'], interactive=True if params['animation'] else False),
            gr.update(choices=expression_list, value=params['expression'],  interactive=True if params['expression'] else False),
            gr.update(interactive=True if params['animation'] else False),
            gr.update(interactive=True if params['expression'] else False),
            gr.update(interactive=True if params['animation'] or params['expression'] else False)]


async def get_models():
    global params
    model_dict = await vtube_studio_functions.get_models(websocket)
    params.update({'model_dict': model_dict})

    current_model = await vtube_studio_functions.get_current_model(websocket)
    if current_model:
        params.update({'model': list(model_dict.keys())[list(model_dict.values()).index(current_model)]})
    else:
        params.update({'model': None})
    return gr.update(choices=list(model_dict.keys()), value=params['model']), gr.update(interactive=True if params['model'] else False),  gr.update(interactive=True if params['model'] else False)


async def load_model(current_model):
    model_id = params['model_dict'][current_model]
    await vtube_studio_functions.load_model(websocket, model_id)
    refreshed_hotkeys = await get_available_hotkeys(model_id)
    return refreshed_hotkeys


def ui():
    global params
    # Gradio elements
    with gr.Accordion("VTube Studio"):
        activate = gr.Checkbox(value=params['activate'], label='Activate VTube Studio')
        with gr.Row():
            host_text = gr.Textbox(value=params['host'], label='Host', placeholder='Leave blank for localhost')
            port_number = gr.Number(value=params['port'], label='Port', precision=0)
            connect_button = gr.Button('Connect')

        with gr.Row():
            model_dropdown = gr.Dropdown(choices=list(params['model_dict'].keys()), value=params['model'], label='VTuber Model')
            model_load_button = gr.Button('Load Model', interactive=True if params['model'] else False)

        model_refresh_button = gr.Button('Refresh',  interactive=True if params['model'] else False)

        with gr.Row():
            animations_dropdown = gr.Dropdown(choices=params['animation_list'], value=params['animation'], label='Animation')
            animation_button = gr.Button('Play Animation', interactive=True if params['animation'] else False)

        with gr.Row():
            expressions_dropdown = gr.Dropdown(choices=params['expression_list'], value=params['expression'], label='Expression')
            expression_button = gr.Button('Play Expression',  interactive=True if params['expression'] else False)

        refresh_hotkeys_button = gr.Button('Refresh', interactive=True if params['animation'] or params['expression'] else False)

    # Event functions to update the parameters in the backend
    activate.change(lambda x: params.update({'activate': x}), activate, None).then(fn=disconnect, inputs=activate, outputs=None)
    model_dropdown.change(lambda x: params.update({'model': x}), model_dropdown, None)
    port_number.change(lambda x: params.update({'port': x}), port_number, None)
    animations_dropdown.change(lambda x: params.update({'animation': x}), animations_dropdown, None)
    expressions_dropdown.change(lambda x: params.update({'expression': x}), expressions_dropdown, None)
    host_text.change(lambda x: params.update({'host': x}), host_text, None)

    # Connect to VTube Studio
    connect_button.click(fn=connect, inputs=None, outputs=None).success(update_menus, outputs=[model_dropdown, model_load_button, model_refresh_button, animations_dropdown, expressions_dropdown, animation_button, expression_button, refresh_hotkeys_button])

    # Play animation
    animation_button.click(fn=play_hotkey, inputs=animations_dropdown)

    # Play expression
    expression_button.click(fn=play_hotkey, inputs=expressions_dropdown)

    # Refresh hotkeys
    refresh_hotkeys_button.click(fn=get_available_hotkeys, inputs=None, outputs=[animations_dropdown, expressions_dropdown, animation_button, expression_button])

    # Refresh models
    model_refresh_button.click(fn=get_models, inputs=None, outputs=[model_dropdown,  model_load_button, model_refresh_button])

    # Load model
    model_load_button.click(fn=load_model, inputs=model_dropdown, outputs=[animations_dropdown, expressions_dropdown, animation_button, expression_button])
