# image_uploader.py
import cloudinary
import cloudinary.uploader
import os
import time
import hashlib
import requests
from dotenv import load_dotenv
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

load_dotenv()


class ImageUploader:
    def __init__(self):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )

    @staticmethod
    def _generate_signature(params, api_secret):
        """Cloudinary signed upload signature banao."""
        to_sign = "&".join(
            f"{k}={v}" for k, v in sorted(params.items()) if v is not None
        )
        to_sign += api_secret
        return hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

    @staticmethod
    def upload_image(parent, image_path, progress_callback=None):
        """
        Upload image to Cloudinary with REAL progress tracking.

        Args:
            parent: Qt parent (unused, kept for compatibility)
            image_path: local file path
            progress_callback: function(percent:int) -> None  (called on each chunk)
        """
        try:
            print(f"Uploading image: {image_path}")

            cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
            api_key = os.getenv("CLOUDINARY_API_KEY")
            api_secret = os.getenv("CLOUDINARY_API_SECRET")

            if not all([cloud_name, api_key, api_secret]):
                return False, "Cloudinary credentials missing in .env"

            timestamp = int(time.time())

            # Signed upload params
            params_to_sign = {"timestamp": timestamp}
            signature = ImageUploader._generate_signature(params_to_sign, api_secret)

            url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

            # File kholo aur multipart banao
            file_size = os.path.getsize(image_path)
            file_handle = open(image_path, "rb")

            fields = {
                "api_key": api_key,
                "timestamp": str(timestamp),
                "signature": signature,
            }

            encoder = MultipartEncoder(
                fields={
                    **fields,
                    "file": (os.path.basename(image_path), file_handle, "application/octet-stream"),
                }
            )

            # ✅ Real progress monitor — har chunk par callback
            last_percent = [-1]

            def _monitor_callback(monitor):
                if progress_callback and file_size > 0:
                    # monitor.bytes_read = kitne bytes bhej diye
                    percent = int((monitor.bytes_read / monitor.len) * 100)
                    if percent > 100:
                        percent = 100
                    if percent != last_percent[0]:
                        last_percent[0] = percent
                        try:
                            progress_callback(percent)
                        except Exception as cb_err:
                            print(f"Progress callback error: {cb_err}")

            monitor = MultipartEncoderMonitor(encoder, _monitor_callback)

            response = requests.post(
                url,
                data=monitor,
                headers={"Content-Type": monitor.content_type},
                timeout=120
            )

            file_handle.close()

            if response.status_code != 200:
                return False, f"HTTP {response.status_code}: {response.text}"

            data = response.json()
            secure_url = data.get("secure_url")
            if not secure_url:
                return False, f"No secure_url in response: {data}"

            print(f"Image uploaded successfully. URL: {secure_url}")
            return True, secure_url

        except Exception as e:
            print(f"Error uploading image: {e}")
            try:
                file_handle.close()
            except Exception:
                pass
            return False, e