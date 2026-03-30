import requests
import json
import os
import base64
import binascii
import random
import time
import re
import math
import logging
from Crypto.Cipher import AES

logger = logging.getLogger(__name__)

class Mega:
    def __init__(self):
        self.sid = None
        self.sequence_num = random.randint(0, 0xFFFFFFFF)
        self.req_id = random.randint(0, 0xFFFFFFFF)
        self.base_url = "https://g.api.mega.co.nz"
        self.user_agent = "Mega.py"

    def login(self, email=None, password=None):
        # login anónimo si no se pasan credenciales
        if not email or not password:
            self.sid = None
            return self
        raise NotImplementedError("Login con usuario/contraseña no implementado en este fork")

    def download_url(self, url, dest_path=None):
        """
        Descarga un archivo desde un enlace MEGA.
        """
        file_id, file_key = self.parse_url(url)
        file_key = self.decode_key(file_key)

        # obtener información del archivo
        info = self.api_request({'a': 'g', 'g': 1, 'p': file_id})
        if 'g' not in info:
            raise ValueError("No se pudo obtener información del archivo")

        file_url = info['g']
        file_name = info.get('at', 'file')
        if dest_path is None:
            dest_path = os.path.join(os.getcwd(), file_name)

        # descargar contenido
        resp = requests.get(file_url, stream=True)
        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)

        return dest_path

    def parse_url(self, url):
        """
        Extrae ID y clave de un enlace MEGA.
        """
        match = re.match(r"https://mega.nz/file/([a-zA-Z0-9_-]+)#([a-zA-Z0-9_-]+)", url)
        if not match:
            raise ValueError("Enlace MEGA inválido")
        return match.group(1), match.group(2)

    def decode_key(self, key):
        """
        Decodifica la clave base64 de MEGA, tolerando longitudes no estándar.
        """
        key += "=" * ((4 - len(key) % 4) % 4)
        try:
            return base64.b64decode(key)
        except binascii.Error:
            raise ValueError("Clave MEGA inválida")

    def api_request(self, data):
        """
        Envía una petición a la API de MEGA.
        """
        self.req_id += 1
        url = f"{self.base_url}/cs?id={self.req_id}"
        resp = requests.post(url, data=json.dumps([data]), headers={'User-Agent': self.user_agent})
        return resp.json()[0]
