# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Define project root using pathlib
PROJECT_ROOT = Path(__file__).resolve().parent


LANGUAGE = "fr"


def get_gettext(lang):
    """translates text to language"""
    import gettext

    path = PROJECT_ROOT / "locale"
    t = gettext.translation(
        "messages",
        path,
        languages=[lang],
        fallback=True,
    )
    t.install()

    if sys.version_info >= (3, 0):
        return lambda message: t.gettext(message)
    else:
        return lambda message: t.ugettext(message)


try:
    lang = os.getenv("INVOICE_LANG", LANGUAGE)
    _ = get_gettext(lang)
except IOError:

    def _(x):
        x

    print("Fix this!")
except ImportError:

    def _(x):
        x

# OS
is_windows = is_linux = False
operating_system = os.name
if operating_system == 'nt': # windows
    is_windows = True
elif operating_system == "posix": # linux/mac
    is_linux = True


class FONT:
    normal = "DejaVu"
    bold = "DejaVu-Bold"


# class PATH:
#     if is_linux:
#         output_dir = Path("~/2_domaines/compta/FACTURATION/Factures/").expanduser()
#     elif is_windows:
#         output_dir = Path("D:/2-Access/ADMIN/compta/FACTURATION/Factures/").expanduser()


# print(f"output: {PATH.output_dir}")


### FONTS

# Define font paths relative to the project root
FONT_PATH = PROJECT_ROOT / "fonts" / "DejaVuSans.ttf"
FONT_BOLD_PATH = PROJECT_ROOT / "fonts" / "DejaVuSans-Bold.ttf"

# Check if the font file exists
if not FONT_PATH.is_file():
    # Fallback to system-wide fonts if the project fonts are not available
    FONT_PATH = Path("/usr/share/fonts/TTF/DejaVuSans.ttf")
    FONT_BOLD_PATH = Path("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf")
# Raise an exception if the fallback fonts are also missing
if not FONT_PATH.is_file():
    raise FileNotFoundError("Fonts not found")
