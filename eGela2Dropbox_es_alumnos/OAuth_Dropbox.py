import urllib.parse
import requests
import webbrowser
import sys
from socket import AF_INET, socket, SOCK_STREAM
import json


def preparacion():
    app_key = 'y9qkbbxfhdib7r3'
    app_secret = 'p1krj5l6hncuz0u'
    redirect_uri = "http://localhost:8090"

###################################################################################
# CODE: Abrir en el navegador la URI https://www.dropbox.com/oauth2/authorize #
###################################################################################
    servidor = 'www.dropbox.com'
    params = {'response_type': 'code', 'client_id': app_key, 'redirect_uri': redirect_uri}
    params_encoded = urllib.parse.urlencode(params)
    recurso = '/oauth2/authorize?' + params_encoded
    uri = 'https://' + servidor + recurso
    webbrowser.open_new(uri)

    # Crear servidor local que escucha por el puerto 8090
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('localHost', 8090))
    server_socket.listen(1)
    print("\tLocal server listening on port 8090")

    # Recibir la solicitude 302 del navegador
    client_connection, client_address = server_socket.accept()
    peticion = client_connection.recv(1024)
    print("\tRequest from the browser received at local server:")

    # Buscar en la petición el "auth_code"
    primera_linea = peticion.decode('UTF8').split('\n')[0]
    print(primera_linea)
    aux_auth_code = primera_linea.split(' ')[1]
    auth_code = aux_auth_code[7:].split('&')[0]
    print("\tauth_code:" + auth_code)

    # Devolver una respuesta al usuario
    http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                    "<html>" \
                    "<head><title>Prueba</title></head>" \
                    "<body>The authentication flow has completed. Close this window.</body>" \
                    "</html>"
    client_connection.sendall(http_response.encode(encoding="utf-8"))
    client_connection.close()
    server_socket.close()

###################################################################################
# ACCESS_TOKEN: Obtener el TOKEN https://www.api.dropboxapi.com/1/oauth2/token #
###################################################################################
    params = {'code': auth_code, 'grant_type': 'authorization_code',
              'client_id': app_key, 'client_secret': app_secret, 'redirect_uri': redirect_uri}
    cabeceras = {'User-Agent': 'Python Client', 'Content-Type': 'application/x-www-form-urlencoded'}
    uri = 'https://api.dropboxapi.com/oauth2/token'
    respuesta = requests.post(uri, headers=cabeceras, data=params)
    print(respuesta.status_code)
    json_respuesta = json.loads(respuesta.content)
    access_token = json_respuesta['access_token']
    print("Access_Token:" + access_token)
    return access_token


#####################################################################################
# USAR APLICACIÓN: /list                                                         #
#####################################################################################
def listarcarpeta():
    access_token = preparacion()
    uri = 'https://api.dropboxapi.com/2/files/list_folder'
    path = sys.argv[2]
    datos = {'path': path}
    datos_encoded = json.dumps(datos)

    print("Datos: " + datos_encoded)
    cabeceras = {'Host': 'api.dropboxapi.com', 'Authorization': 'Bearer ' + access_token,
                 'Content-Type': 'application/json'}
    respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)

    status = respuesta.status_code
    print("\tStatus: " + str(status))
    print("\tReason: " + respuesta.reason)
    contenido = respuesta.text
    print("\tContenido:")
    contenido_json = json.loads(contenido)
    for entrie in contenido_json["entries"]:
        print(entrie['name'])


#####################################################################################
# USAR APLICACIÓN: /upload                                                       #
#####################################################################################
def subirarchivo():
    access_token = preparacion()
    file_path = sys.argv[2]
    with open(file_path, "r") as archivo:
        file_data = archivo.read()

    uri = "https://content.dropboxapi.com/2/files/upload"
    dropbox_api_arg = {'path': sys.argv[3], 'mode': 'add', 'autorename': True, 'mute': False, }
    dropbox_api_arg_json = json.dumps(dropbox_api_arg)
    print("Dropbox-API-Arg header: " + dropbox_api_arg_json)
    cabeceras = {'Host': 'content.dropboxapi.com', 'Authorization': 'Bearer ' + access_token,
                 'Content-Type': 'application/octet-stream',
                 'Dropbox-API-Arg': dropbox_api_arg_json}

    respuesta = requests.post(uri, headers=cabeceras, data=file_data, allow_redirects=False)
    status = respuesta.status_code
    print("\tStatus: " + str(status))
    print("\tReason: " + respuesta.reason)
    contenido = respuesta.text
    print("\tContenido:")
    print(contenido)


#####################################################################################
# USAR APLICACIÓN: /download                                                       #
#####################################################################################
def descargararchivo():
    access_token = preparacion()
    uri = 'https://content.dropboxapi.com/2/files/download'
    path = sys.argv[2]
    datos = {'path': path}
    datos_encoded = json.dumps(datos)
    dropbox_api_arg = {'path': path, }
    dropbox_api_arg_json = json.dumps(dropbox_api_arg)

    print("Datos: " + datos_encoded)
    cabeceras = {'Host': 'content.dropboxapi.com', 'Authorization': 'Bearer ' + access_token,
                 'Dropbox-API-Arg': dropbox_api_arg_json}
    respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)

    status = respuesta.status_code
    print("\tStatus: " + str(status))
    print("\tReason: " + respuesta.reason)


#####################################################################################
# USAR APLICACIÓN: /upload                                                       #
#####################################################################################
def borrararchivo():
    access_token = preparacion()
    uri = 'https://api.dropboxapi.com/2/files/delete_v2'
    path = sys.argv[2]
    datos = {'path': path}
    datos_encoded = json.dumps(datos)

    print("Datos: " + datos_encoded)
    cabeceras = {'Host': 'api.dropboxapi.com', 'Authorization': 'Bearer ' + access_token,
                 'Content-Type': 'application/json'}
    respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)

    status = respuesta.status_code
    print("\tStatus: " + str(status))
    print("\tReason: " + respuesta.reason)


def typo(metodo):
    switcher = {
        "listar": listarcarpeta,
        "subir": subirarchivo,
        "descargar": descargararchivo,
        "eliminar": borrararchivo,
    }
    # Get the function from switcher dictionary
    func = switcher.get(metodo, lambda: "Tipo NO válido")
    # Execute the function
    func()


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("Faltan los parámetros:")
        print("  - listar: metodo, carpeta")
        print("  - subir: metodo, fichero, carpeta")
        print("  - descargar: metodo, fichero")
        print("  - eliminar: metodo, fichero")
    else:
        argument = sys.argv[1]
        typo(argument)
