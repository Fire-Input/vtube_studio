import json
from pathlib import Path
import websockets


# Get the authentication token
async def get_auth_token(websocket):
    auth_file = Path("extensions", "vtube_studio", "auth_token.txt")
    try:
        if auth_file.is_file():
            with open(auth_file, "r") as token_file:
                print(f"Reading authentication token from {auth_file}")
                auth_token = token_file.read().strip()
            print(f"Found authentication token in {auth_file}")
            if auth_token is None:
                raise FileNotFoundError
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print("No authentication token found. Generating one...")
        message = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "AuthenticationTokenRequestID",
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": "AIVTuber",
                "pluginDeveloper": "AIVTuber Dev"
            }
        }
        await websocket.send(json.dumps(message))
        result = await websocket.recv()
        response = json.loads(result)
        if response["messageType"] == "AuthenticationTokenResponse":
            auth_token = response["data"]["authenticationToken"]
            with open(auth_file, "w") as f:
                f.write(auth_token)
            print(f"Authentication token saved to {auth_file}")
        else:
            print("Unexpected response received:", json.dumps(response, indent=4))
    return auth_token


# Authenticate the plugin with the authentication token
async def authenticate(websocket, auth_token):
    message = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "AuthenticationRequestID",
        "messageType": "AuthenticationRequest",
        "data": {
            "pluginName": "AIVTuber",
            "pluginDeveloper": "AIVTuber Dev",
            "authenticationToken": auth_token
        }
    }
    print("Sending authentication request...")
    await websocket.send(json.dumps(message))
    result = await websocket.recv()
    response = json.loads(result)
    if response["messageType"] == "AuthenticationResponse" and response["data"]["authenticated"]:
        print("Plugin authenticated for the duration of this session")
        return True
    else:
        print("Authentication failed:", json.dumps(response, indent=4))
        return False


# Get the current model ID
async def get_current_model(websocket):
    message = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "GetModelID",
        "messageType": "CurrentModelRequest",
    }
    await websocket.send(json.dumps(message))
    result = await websocket.recv()
    data = json.loads(result)
    if data["data"]["modelLoaded"]:
        return json.loads(result)["data"]["modelID"]
    else:
        return None


# Get the hotkeys for the current model
async def get_hotkeys(websocket, model_id=None):
    if not model_id:
        model_id = await get_current_model(websocket)
    message = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "GetHotkeysID",
        "messageType": "HotkeysInCurrentModelRequest",
        "data": {
            "modelID": model_id
        }
    }
    try:
        await websocket.send(json.dumps(message))
        result = await websocket.recv()
        data = json.loads(result)
        # print(json.dumps(data, indent=4))
        expressions = []
        animations = []
        for item in data['data']["availableHotkeys"]:
            if item['type'] == "ToggleExpression":
                expressions.append(item['name'])
            elif item['type'] == "TriggerAnimation":
                animations.append(item['name'])
        return animations, expressions
    except websockets.ConnectionClosed as e:
        print("WebSocket connection closed: ", e)
        return None, None
    except Exception as e:
        print("Error while retrieving hotkeys: ", e)
        return None, None


# Execute a hotkey
async def execute_hotkey(websocket, animation_hotkey=None, expression_hotkey=None):
    # Success flag
    success = False
    # If no hotkeys are specified, return false
    if not animation_hotkey and not expression_hotkey:
        print("No hotkeys specified")
        return False

    # If an expression hotkey is specified, execute it
    if expression_hotkey:
        print("Executing expression hotkey:", expression_hotkey)
        message = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "ExpressionRequestID",
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": expression_hotkey
            }
        }
        await websocket.send(json.dumps(message))
        result = await websocket.recv()
        # If there was an error executing the hotkey, print the error and return false
        try:
            if json.loads(result)["messageType"] == "APIError" or json.loads(result)["data"]["errorID"]:
                print("Expression hotkey failed to execute")
                print(json.dumps(json.loads(result), indent=4))
                return False
            # If the hotkey was successfully executed, set the success flag to true
            else:
                print("Expression hotkey executed successfully")
                success = True
        # If there was no errorID, the hotkey was successfully executed
        except KeyError:
            print("Expression hotkey executed successfully")
            success = True

    # If an animation hotkey is specified, execute it
    if animation_hotkey:
        print("Executing animation hotkey:", animation_hotkey)
        message = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "AnimationRequestID",
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": animation_hotkey
            }
        }
        await websocket.send(json.dumps(message))
        result = await websocket.recv()
        # If there was an error executing the hotkey, print the error and return false
        try:
            if json.loads(result)["messageType"] == "APIError" or json.loads(result)["data"]["errorID"]:
                print("Animation hotkey failed to execute")
                print(json.dumps(json.loads(result), indent=4))
                return False
            # If the hotkey was successfully executed, set the success flag to true
            else:
                print("Animation hotkey executed successfully")
                success = True
        # If there was no errorID, the hotkey was successfully executed
        except KeyError:
            print("Animation hotkey executed successfully")
            success = True

    # Return the success flag
    return success


async def get_models(websocket):
    message = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "GetModelID",
        "messageType": "AvailableModelsRequest",
    }
    await websocket.send(json.dumps(message))
    result = await websocket.recv()
    data = json.loads(result)
    # print(json.dumps(data, indent=4))
    models = {}
    for item in data['data']["availableModels"]:
        models[item['modelName']] = item['modelID']
    return models


async def load_model(websocket, model_name):
    message = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "LoadModelID",
        "messageType": "ModelLoadRequest",
        "data": {
            "modelID": model_name
        }
    }
    await websocket.send(json.dumps(message))
    result = await websocket.recv()
    data = json.loads(result)
    # If there was an error loading the model, print the error and return false
    try:
        if data["messageType"] == "APIError" or data["data"]["errorID"]:
            print("Failed to load model!")
            print(json.dumps(json.loads(result), indent=4))
            return False
        # If the model was successfully loaded, return true
        else:
            print("Model loaded successfully")
            return True
    # If there was no errorID, the model was successfully loaded
    except KeyError:
        print("Model loaded successfully")
        return True
