"""Tool locations, overridable with environment variables (defaults = KiCad.app on macOS).

    KICAD_CLI     kicad-cli executable                    (Linux: e.g. a wrapper around the KiCad flatpak)
    KICAD_SHARE   dir with KiCad's symbols/ and footprints/ libraries
    KICAD_PRO_TEMPLATE  .kicad_pro used as template for the project file (default: the repo's own luchtmeter.kicad_pro)
"""
import os, shutil

MAC_APP = '/Applications/KiCad/KiCad.app/Contents'


def _first(*cands):
    for c in cands:
        if c and os.path.exists(c):
            return c
    return cands[-1]


KICAD_CLI = os.environ.get('KICAD_CLI') or _first(MAC_APP + '/MacOS/kicad-cli', shutil.which('kicad-cli') or 'kicad-cli')
KICAD_SHARE = os.environ.get('KICAD_SHARE') or _first(MAC_APP + '/SharedSupport', '/usr/share/kicad')
_tpl = os.path.expanduser('~/Documents/GitHub/tiltbox-kicad/tiltbox.kicad_pro')
PRO_TEMPLATE = os.environ.get('KICAD_PRO_TEMPLATE') or _first(_tpl, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'luchtmeter.kicad_pro'))
SYMDIR = os.path.join(KICAD_SHARE, 'symbols') + '/'
FPDIR = os.path.join(KICAD_SHARE, 'footprints') + '/'
