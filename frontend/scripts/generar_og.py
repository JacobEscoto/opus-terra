"""Genera las imágenes sociales de OpusTerra."""

from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont


RAIZ = Path(__file__).resolve().parents[1]
COLOR_FONDO = "#0b1220"
COLOR_TEXTO = "#f2eee5"


def fuente_sora(tamano: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Obtiene Sora del proyecto y usa una fuente del sistema como respaldo."""
    carpeta = RAIZ / "node_modules" / "@fontsource-variable" / "sora"
    candidatas = list(carpeta.glob("*.ttf")) + list(carpeta.glob("*.otf"))
    if not candidatas:
        for woff2 in carpeta.glob("*.woff2"):
            temporal = Path(tempfile.mkdtemp()) / "sora.ttf"
            copia = temporal.with_suffix(".woff2")
            shutil.copyfile(woff2, copia)
            try:
                subprocess.run(["woff2_decompress", str(copia)], check=True, capture_output=True)
                candidatas.append(temporal)
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass
    candidatas += [Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf")]
    return ImageFont.truetype(str(candidatas[0]), tamano)


def dibujar(ruta: Path, lado: int, cuadrada: bool = False) -> None:
    imagen = Image.new("RGB", (lado, lado if cuadrada else 630), COLOR_FONDO)
    dibujo = ImageDraw.Draw(imagen)
    ancho, alto = imagen.size
    margen = 92 if not cuadrada else 110
    titulo = fuente_sora(88 if not cuadrada else 96)
    subtitulo = fuente_sora(31 if not cuadrada else 35)
    dibujo.text((margen, alto * 0.29), "OpusTerra", fill=COLOR_TEXTO, font=titulo)
    dibujo.text(
        (margen, alto * 0.29 + 115),
        "Cambios ambientales en el planeta, con datos de la NASA",
        fill="#aeb9ca",
        font=subtitulo,
    )
    centro = (ancho - 190, alto // 2 + 20)
    radio = 122 if not cuadrada else 180
    dibujo.ellipse(
        (centro[0] - radio, centro[1] - radio, centro[0] + radio, centro[1] + radio),
        fill="#3988c2",
        outline="#d99435",
        width=9,
    )
    dibujo.arc(
        (centro[0] - radio + 22, centro[1] - radio + 22, centro[0] + radio - 22, centro[1] + radio - 22),
        205,
        25,
        fill="#d99435",
        width=15,
    )
    imagen.save(ruta, "PNG")


if __name__ == "__main__":
    dibujar(RAIZ / "public" / "og-image.png", 1200)
    dibujar(RAIZ / "public" / "og-image-cuadrada.png", 1200, cuadrada=True)
