from adaptadores.fuente_red import FuenteRed

fuente = FuenteRed()
print(fuente.listar_criptas())
print("Solicitudes hechas:", fuente.solicitudes)