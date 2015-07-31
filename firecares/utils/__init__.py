from PIL import Image


def convert_png_to_jpg(img):
    """
    Converts a png to a jpg.
    :param img: Absolute path to the image.
    :returns: the filename
    """
    im = Image.open(img)
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, im)
    filename = img.replace('png', 'jpg')
    bg.save(filename, quality=85)
    return filename
