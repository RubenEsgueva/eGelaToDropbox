# -*- coding: UTF-8 -*-
import json
import os
from tkinter import messagebox
import requests
import urllib
from urllib.parse import unquote
from bs4 import BeautifulSoup
import time
import helper


class eGela:
    _login = 0
    _cookie = ""
    _webegela = ""
    _curso = ""
    _refs = []
    _root = None

    def __init__(self, root):
        self._root = root

    def check_credentials(self, username, password, event=None):
        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("##### 1. PETICION #####")
        metodo = 'GET'
        uri = "https://egela.ehu.eus/login/index.php"
        cabeceras = {'Host': 'egela.ehu.eus'}
        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)
        print(metodo + " " + uri)
        print(str(respuesta.status_code) + " " + respuesta.reason)
        direct = ""
        galleta = ""
        if 'Location' in respuesta.headers:
            direct = respuesta.headers['Location']
        if 'Set-Cookie' in respuesta.headers:
            galleta = respuesta.headers['Set-Cookie']
            galleta = galleta.split(";")[0]
        html_pulido = BeautifulSoup(respuesta.content, "html.parser")
        tokenlogin = html_pulido.find('input', {'name': 'logintoken'})['value']
        print(uri + " " + galleta)

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 2. PETICION #####")
        metodo = 'POST'
        cabeceras = {'Host': 'egela.ehu.eus', 'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': galleta}
        cuerpo = {'logintoken': tokenlogin, 'username': username.get(), 'password': password.get()}
        cuerpo_encoded = urllib.parse.urlencode(cuerpo)
        cabeceras['Content-Length'] = str(len(cuerpo_encoded))
        respuesta = requests.request(metodo, uri, data=cuerpo_encoded, headers=cabeceras, allow_redirects=False)
        print(metodo + " " + uri)
        print(str(respuesta.status_code) + " " + respuesta.reason)
        direct = ""
        galleta = ""
        if 'Location' in respuesta.headers:
            direct = respuesta.headers['Location']
        if 'Set-Cookie' in respuesta.headers:
            galleta = respuesta.headers['Set-Cookie']
            galleta = galleta.split(";")[0]
        print(direct + " " + galleta)
        if 'testsession' in direct:
            logeado = True
        else:
            logeado = False

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 3. PETICION #####")
        metodo = 'GET'
        uri = direct
        cabeceras = {'Host': 'egela.ehu.eus', 'Cookie': galleta}
        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)
        print(metodo + " " + uri)
        print(str(respuesta.status_code) + " " + respuesta.reason)
        direct = ""
        if 'Location' in respuesta.headers:
            direct = respuesta.headers['Location']
        if 'set-cookie' in respuesta.headers:
            galleta = respuesta.headers['set-cookie']
            galleta = galleta.split(";")[0]
        print(direct + " " + galleta)

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        print("\n##### 4. PETICION #####")
        metodo = 'GET'
        uri = direct
        cabeceras = {'Host': 'egela.ehu.eus', 'Cookie': galleta}
        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=True)
        print(metodo + " " + uri)
        print(str(respuesta.status_code) + " " + respuesta.reason)
        web_egela = respuesta.content

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        if logeado:
            self._login = 1
            self._cookie = galleta
            self._webegela = web_egela
            self._root.destroy()
        else:
            messagebox.showinfo("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### 4. PETICION (Página principal de la asignatura en eGela) #####")

        #buscamos enlace de curso de sw en la pagina de egela
        doc = BeautifulSoup(self._webegela, 'html.parser')
        enlaces = doc.html.body.find_all('a')
        for e in enlaces:
            if e.text == 'Sistemas Web':
                self._curso = e['href']
                break

        metodo = 'GET'
        uri = self._curso
        cabeceras = {'Host': 'egela.ehu.eus', 'Content-Type': 'application/x-www-form-urlencoded',
                     'Cookie': self._cookie}
        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)
        print("Petición curso Sistemas Web:")
        print("Método: " + str(metodo) + ", URI: " + str(uri))
        codigo = respuesta.status_code
        descripcion = respuesta.reason
        cuerpo = respuesta.content
        print(str(codigo) + " " + descripcion)


        print("\n##### Analisis del HTML... #####")
        #############################################
        # ANALISIS DE LA PAGINA DEL AULA EN EGELA
        # PARA BUSCAR PDFs:

        doc = BeautifulSoup(cuerpo, 'html.parser')
        enlaces = doc.html.body.find_all('a', {'class': 'aalink'})
        NUMERO_DE_PDF_EN_EGELA = len(enlaces)
        for e in enlaces:
            if e.img['src'].endswith("pdf"):
                span_element = e.find('span', class_='instancename')
                nombre = span_element.text
                link = e['href']
                par = {'pdf_name': nombre, 'pdf_link': link}
                par = json.dumps(par)
                self._refs.append(par)
                NUMERO_DE_PDF_EN_EGELA += 1

                # INICIALIZA Y ACTUALIZAR BARRA DE PROGRESO
                # POR CADA PDF ANIADIDO EN self._refs

                progress_step = float(100.0 / NUMERO_DE_PDF_EN_EGELA)

                progress += progress_step
                progress_var.set(progress)
                progress_bar.update()
                time.sleep(0.1)

        popup.destroy()
        return self._refs

    def get_pdf(self, selection):

        pdf = self._refs[selection]
        pdf = json.loads(pdf)
        uri_sel = pdf['pdf_link']
        pdf_name = pdf['pdf_name']
        print("\t##### descargando  PDF... #####")
        #############################################

        metodo = 'GET'
        uri = uri_sel
        cabeceras = {'Host': 'egela.ehu.eus', 'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': self._cookie}
        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)
        nuevaURI = respuesta.headers['Location']

        metodo = 'GET'
        uri = nuevaURI
        cabeceras = {'Host': 'egela.ehu.eus', 'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': self._cookie}
        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)

        pdf_content = respuesta.content

        return pdf_name, pdf_content