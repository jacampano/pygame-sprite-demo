# Demo de sprite con Pygame

Proyecto mínimo para visualizar y probar animaciones de un personaje estilo plataformas 2D usando Pygame.

## Requisitos

- Python 3.10 o superior
- `pip install -r requirements.txt`

## Ejecución

```bash
python main.py
```

## Controles

- `A` / `D` o flechas izquierda/derecha: mover
- `Shift`: correr
- `Espacio`: saltar
- `J`: atacar
- `H`: recibir daño
- `K`: morir
- `R`: reiniciar personaje
- `Esc`: salir

## Estructura

- `main.py`: demo principal
- `assets/original_sheet.png`: hoja original generada
- `assets/frames/`: frames recortados usados por el juego

## Nota

Los frames se han extraído de la hoja que generamos previamente para montar una demo funcional rápida. Si quieres, en el siguiente paso puedo prepararte una versión mejor organizada con:

- sprite sheet limpio sin textos ni paneles,
- colisiones más precisas,
- cámara lateral,
- scroll de escenario,
- exportación a atlas para motores 2D.
