import shutil
import tempfile

from django.test import LiveServerTestCase, TestCase, override_settings


STORAGE_SETTINGS = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}


class StorageOverrideMixin:
    @classmethod
    def setUpClass(cls):
        cls._temp_media = tempfile.mkdtemp()
        cls._override = override_settings(
            MEDIA_ROOT=cls._temp_media,
            STORAGES=STORAGE_SETTINGS,
            STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
        )
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._temp_media, ignore_errors=True)


class BaseTestCase(StorageOverrideMixin, TestCase):
    pass


class BaseLiveServerTestCase(StorageOverrideMixin, LiveServerTestCase):
    pass
