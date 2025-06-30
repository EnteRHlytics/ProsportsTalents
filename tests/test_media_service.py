import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.media_service import MediaService


def test_create_thumbnail(tmp_path):
    img_path = tmp_path / "img.jpg"
    Image.new('RGB', (800, 600), color='red').save(img_path)

    thumb_path = MediaService.create_thumbnail(str(img_path), size=(100, 100))
    assert os.path.exists(thumb_path)
    with Image.open(thumb_path) as thumb:
        width, height = thumb.size
        assert width <= 100 and height <= 100


def test_compress_image(tmp_path):
    img_path = tmp_path / "img.jpg"
    Image.new('RGB', (800, 600), color='blue').save(img_path, quality=100)
    original_size = img_path.stat().st_size

    MediaService.compress_image(str(img_path), quality=50)
    compressed_size = img_path.stat().st_size
    assert compressed_size <= original_size


def test_save_image_with_options(tmp_path):
    img_path = tmp_path / "upload.jpg"
    Image.new('RGB', (500, 400), color='green').save(img_path)

    class FileStorageMock:
        filename = 'upload.jpg'
        def save(self, dst):
            Image.open(img_path).save(dst)

    path, filename, thumb = MediaService.save_image(
        FileStorageMock(), 'a1', 'photos', create_thumbnail=True, compress=True, thumbnail_size=(50, 50), quality=40
    )

    assert os.path.exists(path)
    assert os.path.exists(thumb)
    assert filename in path
