import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = 'y9qkbbxfhdib7r3'
app_secret = 'p1krj5l6hncuz0u'
server_addr = "localhost"
server_port = 8090
redirect_uri = "http://" + server_addr + ":" + str(server_port)


class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        servidor = 'www.dropbox.com'
        params = {'response_type': 'code', 'client_id': app_key, 'redirect_uri': redirect_uri}

        params_encoded = urllib.parse.urlencode(params)
        recurso = '/oauth2/authorize?' + params_encoded
        uri = 'https://' + servidor + recurso
        webbrowser.open_new(uri)

        # por el puerto 8090 esta escuchando el servidor que generamos
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # recibe la redireccion 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print(peticion)

        # buscar en solicitud el "auth_code"
        primera_linea = peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print("\tauth_code: " + auth_code)

        # devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response.encode(encoding="utf-8"))
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        auth_code = self.local_server()
        params = {'code': auth_code, 'grant_type': 'authorization_code',
                  'client_id': app_key, 'client_secret': app_secret, 'redirect_uri': redirect_uri}
        cabeceras = {'User-Agent': 'Python Client', 'Content-Type': 'application/x-www-form-urlencoded'}
        uri = 'https://api.dropboxapi.com/oauth2/token'
        respuesta = requests.post(uri, headers=cabeceras, data=params)
        self._root.destroy()
        print("Code do_oAuth: " + str(respuesta.status_code))
        json_respuesta = json.loads(respuesta.content)
        self._access_token = json_respuesta['access_token']
        print("Access_Token:" + str(self._access_token))

    def list_folder(self, msg_listbox):
        print("/list_folder")
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        access_token = self._access_token
        datos = {'path': msg_listbox}
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

        self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)

    def transfer_file(self, file_path, a_subir):
        print("/upload")
        with open(a_subir, "r") as archivo:
            file_data = archivo.read()
        uri = "https://content.dropboxapi.com/2/files/upload"
        access_token = self._access_token
        dropbox_api_arg = {'path': file_path, 'mode': 'add', 'autorename': True, 'mute': False, }
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

    def delete_file(self, file_path):
        print("/delete_file")
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        access_token = self._access_token
        datos = {'path': file_path}
        datos_encoded = json.dumps(datos)

        print("Datos: " + datos_encoded)
        cabeceras = {'Host': 'api.dropboxapi.com', 'Authorization': 'Bearer ' + access_token,
                     'Content-Type': 'application/json'}
        respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)

        status = respuesta.status_code
        print("\tStatus: " + str(status))
        print("\tReason: " + respuesta.reason)

    def create_folder(self, path):
        print("/create_folder")
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
        access_token = self._access_token
        datos = {'autorename': False, 'path': path}
        datos_encoded = json.dumps(datos)

        print("Datos: " + datos_encoded)
        cabeceras = {'Host': 'api.dropboxapi.com', 'Authorization': 'Bearer ' + access_token,
                     'Content-Type': 'application/json'}
        respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)

        status = respuesta.status_code
        print("\tStatus: " + str(status))
        print("\tReason: " + respuesta.reason)
