import os
from uuid import uuid4
from flask import Flask, g, jsonify, abort, send_file, url_for, request, make_response
from flask.views import MethodView
from veracrypt import Volume, VolumeManager


def to_json(volume: Volume):
    is_mounted = volume.is_mounted()
    links = [{"rel": "self", "href": url_for("volume", name=volume.name)}]

    if is_mounted:
        links.append(
            {"rel": "files", "href": url_for("volume_files", name=volume.name)}
        )

    return {"name": volume.name, "mounted": is_mounted, "_links": links}


class BaseAPI(MethodView):

    def __init__(self, manager: VolumeManager):
        self.manager = manager

    def get_volume(self, name):
        volume = self.manager.get_volume(name)

        if volume is None:
            abort(404)

        return volume


class VolumesAPI(BaseAPI):

    def get(self):
        response = {
            "volumes": [to_json(v) for v in self.manager.get_volumes()],
            "_links": [{"rel": "self", "href": url_for("volumes")}],
        }
        return jsonify(response)


class VolumeAPI(BaseAPI):

    def get(self, name):
        volume = self.get_volume(name)
        return jsonify(to_json(volume))

    def put(self, name):
        volume = self.get_volume(name)
        options = request.get_json()
        password = options.get("password", "") if isinstance(options, dict) else ""

        if not volume.is_mounted():
            try:
                volume.mount(password, os.path.join("/tmp", uuid4().hex))
            except:
                abort(401)

        return jsonify(to_json(volume))

    def delete(self, name):
        volume = self.get_volume(name)

        if volume.is_mounted():
            volume.unmount()

        return jsonify(to_json(volume))


class VolumeFilesAPI(BaseAPI):

    def get(self, name, path=""):
        volume = self.get_volume(name)

        if not volume.is_mounted():
            abort(400)

        mount_path = volume.get_mount_path()
        full_path = os.path.join(mount_path, path)

        if not os.path.abspath(full_path).startswith(mount_path):
            abort(400)

        if os.path.isfile(full_path):
            return send_file(full_path)

        if os.path.isdir(full_path):
            _, dirnames, filenames = next(os.walk(full_path))
            response = {
                "directories": dirnames,
                "files": filenames,
                "_links": [
                    {"rel": "self", "href": url_for("volume_files", name=volume.name)}
                ],
            }
            return jsonify(response)

        abort(404)


def make_app(manager: VolumeManager):
    app = Flask(__name__)

    volumes_view = VolumesAPI.as_view("volumes", manager=manager)
    volume_view = VolumeAPI.as_view("volume", manager=manager)
    volume_files_view = VolumeFilesAPI.as_view("volume_files", manager=manager)

    app.add_url_rule("/volumes", view_func=volumes_view)
    app.add_url_rule("/volumes/<name>", view_func=volume_view)
    app.add_url_rule("/volumes/<name>/files", view_func=volume_files_view)
    app.add_url_rule("/volumes/<name>/files/<path:path>", view_func=volume_files_view)

    return app


VOLUMES_PATH = os.path.join(os.getcwd(), "volumes")
app = make_app(VolumeManager(VOLUMES_PATH))
