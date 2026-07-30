import pytest
from PIL import Image

from auto_classes.ui import assets


def test_shipped_icons_exist():
    for name in (assets.IMPORT_ICON, assets.PRONOTE_ICON):
        assert (assets.ASSETS_DIR / name).is_file()


def test_load_returns_rgba():
    image = assets._load(assets.IMPORT_ICON)
    assert image.mode == "RGBA"


def test_load_is_cached():
    assert assets._load(assets.IMPORT_ICON) is assets._load(assets.IMPORT_ICON)


def test_missing_asset_is_reported_clearly():
    with pytest.raises(FileNotFoundError, match="absente du paquet"):
        assets._load("inexistant.png")


def test_recolored_keeps_transparency_and_repaints_pixels():
    source = assets._load(assets.IMPORT_ICON)
    tinted = assets._recolored(assets.IMPORT_ICON, "#FF0000")

    assert tinted.size == source.size
    assert list(tinted.getchannel("A").getdata()) == list(source.getchannel("A").getdata())

    opaque = [
        pixel[:3] for pixel in tinted.getdata() if pixel[3] == 255
    ]
    assert opaque, "le pictogramme doit avoir des pixels opaques"
    assert set(opaque) == {(255, 0, 0)}


def test_recolored_does_not_touch_the_cached_source():
    assets._recolored(assets.IMPORT_ICON, "#FF0000")
    source = assets._load(assets.IMPORT_ICON)
    assert source.getpixel((0, 0))[3] == 0  # coin resté transparent


def test_icon_builds_without_a_tk_root():
    image = assets.icon(assets.IMPORT_ICON, size=18, tint=("#000000", "#FFFFFF"))
    assert image.cget("size") == (18, 18)


def test_icon_without_tint_uses_the_same_image_for_both_themes():
    image = assets.icon(assets.PRONOTE_ICON, size=20)
    assert image.cget("light_image") is image.cget("dark_image")


def test_icon_with_tint_differs_between_themes():
    image = assets.icon(assets.IMPORT_ICON, size=20, tint=("#000000", "#FFFFFF"))
    assert image.cget("light_image") is not image.cget("dark_image")


def test_icon_is_not_recycled_between_calls():
    """Chaque appel doit rendre une CTkImage neuve : elles sont liées à une racine Tk."""
    first = assets.icon(assets.PRONOTE_ICON, size=18)
    second = assets.icon(assets.PRONOTE_ICON, size=18)
    assert first is not second


def test_pronote_icon_carries_the_brand_colors():
    colors = {pixel[:3] for pixel in assets._load(assets.PRONOTE_ICON).getdata() if pixel[3] == 255}

    def close(target, tolerance=6):
        return any(
            all(abs(channel - expected) <= tolerance for channel, expected in zip(color, target))
            for color in colors
        )

    assert close(Image.new("RGB", (1, 1), "#018673").getpixel((0, 0)))
    assert close(Image.new("RGB", (1, 1), "#FECD06").getpixel((0, 0)))
