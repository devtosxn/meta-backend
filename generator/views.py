from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from pathlib import Path
# from numpy.random.mtrand import f
from solid.objects import union, translate
from solid.solidpython import scad_render_to_file
from django.views.decorators.csrf import csrf_exempt
import tempfile
from .generator import gen_form
import secrets
import subprocess
# Create your views here.
import boto3
import json
import math
import os


bucket = os.environ.get('BUCKET_NAME')
ACCESS_KEY_ID = os.environ.get('ACCESS_KEY_ID')
SECRET_ACCESS_KEY = os.environ.get('SECRET_ACCESS_KEY')
REGION = os.environ.get('REGION')

s3 = boto3.client('s3',
                  aws_access_key_id=ACCESS_KEY_ID,
                  aws_secret_access_key=SECRET_ACCESS_KEY,
                  region_name=REGION
                  )


@csrf_exempt
def generator(request):

    spacing = 100
    if request.method == 'POST':
        data = json.loads(request.body)
        buildings = int(data.get("# of buildings"))
        ceiling_height = float(data.get('Ceiling Height'))
        chaos = float(data.get('Chaos value'))
        no_of_rooms = int(data.get("Number of rooms"))
        square_footage = float(data.get("Square footages"))
        length = math.sqrt(square_footage)
        width = math.sqrt(square_footage)

        # print(data)
        # print(buildings)
        # print(ceiling_height)
        # print(chaos)
        # print(no_of_rooms)
        houses = None
        forms = list()
        with tempfile.TemporaryDirectory() as tempdir:
            for number in range(buildings):
                form = gen_form(chaos, ceiling_height, no_of_rooms,
                                length, width, fractalize=False, make_roof=False)
                layer = number // buildings
                j = number % (buildings**2)
                x, y = spacing*(j//buildings), spacing*(j % buildings)
                z = spacing * layer
                forms.append(translate([x, y, z],)(form))

            houses = union()(forms)
            file = f"{tempdir}/{secrets.token_hex()}.scad"
            file_name, ext = file.split(".")
            scad_render_to_file(houses, file)
            subprocess.run(["openscad", "-o", f"{file_name}.stl", file])
            key = file_name.split("/")[-1]
            print("The Key:", key)
            s3.upload_file(
                Filename=f"{file_name}.stl",
                Bucket="metakitex",
                Key=f"{key}.stl",
                ExtraArgs={"ACL": "public-read"}
            )
            url = f"https://{bucket}.s3.amazonaws.com/{key}.stl"

        return JsonResponse({"url": url})
