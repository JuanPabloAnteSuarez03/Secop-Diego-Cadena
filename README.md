# Secop-Diego-Cadena
Create installer:
pyinstaller --noconfirm --clean --windowed --name ModeloPredictivo --icon "src\ui\assets\app.ico" --add-data "data\base_datos_app.db;data" --add-data "data\modelo_entrenado.pkl;data" --add-data "src\ui\assets;src\ui\assets" src\main.py