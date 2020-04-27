echo@off
set root = C:\Users\JGC\Desktop\Trabalhos\Python\Machadobot
cd %root%
call activate base
start C:\Users\JGC\anaconda3\pythonw.exe "%~dp0\machadobot\machado.py"
call conda deactivate
exit