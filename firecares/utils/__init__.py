from django.core.files.storage import get_storage_class
from storages.backends.s3boto import S3BotoStorage
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


class CachedS3BotoStorage(S3BotoStorage):
    """
    S3 storage backend that saves the files locally, too.
    """
    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage")()

    def save(self, name, content):
        name = super(CachedS3BotoStorage, self).save(name, content)
        self.local_storage._save(name, content)
        return name


def dictfetchall(cursor):
    """
    Returns all rows from a cursor as a dict
    """
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]
