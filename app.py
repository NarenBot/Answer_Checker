from flask import Flask, render_template, request, jsonify
import boto3
from werkzeug.utils import secure_filename
from trp import Document
import os

from utils import inputDataExcel


app = Flask(__name__)

ACCESS_KEY_ID = "AKIAQULFVLB7QTQSS6NH"
ACCESS_SECRET_KEY = "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"
BUCKET_NAME = "narenineuron"

s3 = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_SECRET_KEY,
)

# Amazon Textract client
textract = boto3.client(
    "textract",
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_SECRET_KEY,
    region_name="ap-south-1",
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["post"])
def upload():
    if request.method == "POST":
        img = request.files["file"]
        if img:
            filename = secure_filename(img.filename)
            img.save("images/temp/" + filename)
            s3.upload_file(
                Bucket=BUCKET_NAME, Filename="images/" + filename, Key=filename
            )
            msg = f"{filename} uploaded into S3 Bucket! "
        else:
            msg = "Please choose the file above and click the upload button."

    return render_template("index.html", msg=msg)


@app.route("/delete")
def delete():
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
    # print(objects["KeyCount"])

    if objects["KeyCount"] != 0:
        ls = []
        for obj in objects["Contents"]:
            ls.append(obj["Key"])
        for filename in ls:
            s3.delete_object(Bucket=BUCKET_NAME, Key=filename)

        msg = f"Objects have been deleted!"
    else:
        msg = f"Fine! Now you can upload your file."

    return render_template("index.html", msg=msg)


@app.route("/extract", methods=["post"])
def extract():
    if request.method == "POST":
        objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
        # print(objects["KeyCount"])

        if objects["KeyCount"] != 0:
            ls = []
            for obj in objects["Contents"]:
                ls.append(obj["Key"])

            text = []
            for filename in ls:
                response = textract.detect_document_text(
                    Document={"S3Object": {"Bucket": BUCKET_NAME, "Name": filename}}
                )

                for item in response["Blocks"]:
                    if item["BlockType"] == "LINE":
                        # print("\033[92m" + item["Text"] + "\033[92m")
                        # print(item["Text"])
                        text.append(item["Text"])

            answer = " ".join(text)

            return render_template("index.html", text=answer)
        else:
            return render_template(
                "index.html",
                msg="Please upload any image into S3 and click extract button",
            )


@app.route("/evaluate", methods=["GET"])
def evaluate():
    if request.method == "GET":
        objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if objects["KeyCount"] != 0:
            ls = []
            for obj in objects["Contents"]:
                ls.append(obj["Key"])

            text = []
            for filename in ls:
                response = textract.detect_document_text(
                    Document={"S3Object": {"Bucket": BUCKET_NAME, "Name": filename}}
                )
                for item in response["Blocks"]:
                    if item["BlockType"] == "LINE":
                        # print("\033[92m" + item["Text"] + "\033[92m")
                        # print(item["Text"])
                        text.append(item["Text"])
            answer = " ".join(text).lower()
            id = int(answer[:2]) - 23
            print(id)

        inputDataExcel(answer=answer, id=id)

    return render_template(
        "index.html", msg="Evaluation Completed. Please check the report."
    )


if __name__ == "__main__":
    app.run(debug=True)
