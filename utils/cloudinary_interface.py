import cloudinary.uploader


class CloudinaryInterface:
    @classmethod
    def upload_file(cls, file, folder_name=""):
        upload_data = cloudinary.uploader.upload_large(
            file, folder=str(folder_name), resource_type="raw"
        )

        url = upload_data.get("url")
        return dict(url=url)
