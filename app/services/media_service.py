import os
import uuid
import logging
from werkzeug.utils import secure_filename
from PIL import Image

class MediaService:
    BASE_DIR = 'storage'

    @staticmethod
    def athlete_media_path(athlete_id, media_type):
        return os.path.join(MediaService.BASE_DIR, 'athletes', athlete_id, media_type)

    @staticmethod
    def save_file(file_storage, athlete_id, media_type):
        directory = MediaService.athlete_media_path(athlete_id, media_type)
        os.makedirs(directory, exist_ok=True)
        ext = os.path.splitext(file_storage.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(directory, secure_filename(filename))
        file_storage.save(path)
        logging.getLogger(__name__).info("Saved media file %s", path)
        return path, filename

    @staticmethod
    def delete_file(path):
        try:
            os.remove(path)
            logging.getLogger(__name__).info("Deleted media file %s", path)
        except FileNotFoundError:
            pass

    @staticmethod
    def create_thumbnail(image_path, size=(128, 128)):
        """Create a thumbnail for the given image and return the path."""
        img = Image.open(image_path)
        img.thumbnail(size)
        base, ext = os.path.splitext(image_path)
        thumb_path = f"{base}_thumb{ext}"
        img.save(thumb_path)
        return thumb_path

    @staticmethod
    def compress_image(image_path, quality=80):
        """Compress an image in-place using the specified quality."""
        img = Image.open(image_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(image_path, optimize=True, quality=quality)
        return image_path

    @staticmethod
    def save_image(file_storage, athlete_id, media_type,
                   create_thumbnail=False, thumbnail_size=(128, 128),
                   compress=False, quality=80):
        """Save an uploaded image with optional compression and thumbnail."""
        path, filename = MediaService.save_file(file_storage, athlete_id, media_type)
        if compress:
            MediaService.compress_image(path, quality=quality)
        thumb_path = None
        if create_thumbnail:
            thumb_path = MediaService.create_thumbnail(path, size=thumbnail_size)
        return path, filename, thumb_path
