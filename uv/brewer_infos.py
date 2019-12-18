from __future__ import annotations

# Map brewer types to whether they need straylight correction
brewer_types = {
    "mki": True,
    "mkii": True,
    "mkiii": False,
    "mkvi": True,
}


def correct_straylight(brewer_type: str):
    if brewer_type in brewer_types:
        return brewer_types[brewer_type]
    else:
        return True
