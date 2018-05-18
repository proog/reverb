import os
import shutil

VOLUMES_PATH = os.path.abspath(".testvolumes")


def reset_test_data():
    shutil.rmtree(VOLUMES_PATH, ignore_errors=True)
    os.mkdir(VOLUMES_PATH)
    shutil.copy("test-volume.vc", os.path.join(VOLUMES_PATH, "test"))
