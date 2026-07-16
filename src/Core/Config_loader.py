import os
import json

def cargar_credenciales():
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    # Buscamos el archivo subiendo dos carpetas (salimos de Core, luego de src) y entrando a config
    ruta_json = os.path.abspath(os.path.join(ruta_actual, "../../config/credentials.json"))

    try:
        with open(ruta_json, "r", encoding="utf-8") as archivo:
            credenciales = json.load(archivo)
            return credenciales
    except FileNotFoundError:
        print('Error al cargar el archivo de configuración. Asegúrese de que el archivo "credentials.json" exista en la carpeta "config" y tenga un formato JSON válido.')
        return None
    
    except json.JSONDecodeError:
        print('El archivo tiene un formato json dañado favor de arreglarlo')
        return None
    
def cargar_ajustes():
    """NUEVA FUNCIÓN: Lee el archivo settings.json para saber tu nombre y la voz creada en eleven labs"""
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_json = os.path.abspath(os.path.join(ruta_actual, "../../config/settings.json"))
    #aqui verifica el json que se creo en la carpeta de config 
    try:
        with open(ruta_json, "r", encoding="utf-8") as archivo:
            ajustes = json.load(archivo)
            return ajustes
    except FileNotFoundError:
        print('Error al cargar los ajustes. Asegúrese de que el archivo "settings.json" exista en la carpeta "config".')
        return None
    except json.JSONDecodeError:
        print('El archivo settings.json tiene un formato json dañado favor de arreglarlo')
        return None

    if __name__ == "__main__":
        datos = cargar_credenciales()
        ajustes = cargar_ajustes()
        if datos:
            print("Credenciales cargadas correctamente:")
        if ajustes:
            print("Ajustes cargados correctamente:")
        else:
            print("No se pudieron cargar las credenciales o ajustes.")