import os.path
from flask import Flask
from veracrypt import VolumeManager
from endpoints import RootAPI, VolumesAPI, VolumeAPI, FilesAPI


def make_app(manager: VolumeManager):
    app = Flask(__name__)

    root_view = RootAPI.as_view(RootAPI.view_name)
    volumes_view = VolumesAPI.as_view(VolumesAPI.view_name, manager=manager)
    volume_view = VolumeAPI.as_view(VolumeAPI.view_name, manager=manager)
    files_view = FilesAPI.as_view(FilesAPI.view_name, manager=manager)

    app.add_url_rule("/", view_func=root_view)
    app.add_url_rule("/volumes", view_func=volumes_view, strict_slashes=False)
    app.add_url_rule("/volumes/<name>", view_func=volume_view)
    app.add_url_rule(
        "/volumes/<name>/files", view_func=files_view, strict_slashes=False
    )
    app.add_url_rule("/volumes/<name>/files/<path:path>", view_func=files_view)

    return app


volume_dir = os.path.join(os.getcwd(), "volumes")
manager = VolumeManager(volume_dir)
app = make_app(manager)
