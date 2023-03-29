from model.colormap import CUSTOM_COLORMAP

BONE_CT = {
    "transferFunction": {
        "scalarOpacityRange": [184.129411764706, 2271.070588235294],
    },
    "colorMap": CUSTOM_COLORMAP.get("STANDARD_CT"),
}

ANGIO_CT = {
    "transferFunction": {
        "scalarOpacityRange": [125.42352941176478, 1785],
    },
    "colorMap": CUSTOM_COLORMAP.get("STANDARD_CT"),
}

MUSCLE_CT = {
    "transferFunction": {
        "scalarOpacityRange": [-63.16470588235279, 559.1764705882356],
    },
    "colorMap": CUSTOM_COLORMAP.get("STANDARD_CT"),
}

MIP = {
    "transferFunction": {
        "scalarOpacityRange": [-1661.5882352941176, 2449.5490196078435]
    },
    "colorMap": CUSTOM_COLORMAP.get("BLACK_TO_WHITE"),
}