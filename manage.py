#!/usr/bin/env python3
import os
import urllib3
from mimetypes import guess_type
from pydantic import BaseSettings
from signa import Factory as SignaFactory
from jinja2 import Environment, FileSystemLoader, select_autoescape


class Settings(BaseSettings):
    htdocs_root: str = 'htdocs' 
    aws_access_key_id: str
    aws_secret_access_key: str
    s3_bucket: str
    s3_region: str
    s3_endpoint: str

    class Config:
        env_file = '.env'


def main():
    publish()


def build():
    """Build site."""
    jinja = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape()
    )
    template = jinja.get_template('index.html')
    html = template.render(
        message='Yo!'
    )
    print(html)


def publish():
    """Build and publish to site S3."""
    build()
    upload_to_s3()


def upload_to_s3():
    """Upload files to S3."""
    settings = Settings()

    # Set up HTTP client
    http = urllib3.PoolManager()

    # Set up request signer
    s3_signer = SignaFactory(
        's3',
        region=settings.s3_region,
        bucket=settings.s3_bucket,
        payload='UNSIGNED-PAYLOAD',
        auth={
            'access_key': settings.aws_access_key_id,
            'secret_key': settings.aws_secret_access_key,
        },
        endpoint=settings.s3_endpoint
    )

    # Set up directory to scan
    directory = settings.htdocs_root

    # Loop through files in directory
    for root, _, files in os.walk(directory):
        for file in files:
            # Set up file path and S3 key
            file_path = os.path.join(root, file)
            s3_key = file_path.replace(directory, '').lstrip('/')

            # Set up HTTP request
            content_type = guess_type(file_path)[0]
            if not content_type:
                print(f"Skipping {file_path} (unknown content type)")
                continue
            headers = {
                'x-amz-acl': 'public-read',
                'content-type': guess_type(file_path)[0],
            }
            signature =  s3_signer.new(
                method='PUT', key=s3_key, headers=headers
            )
            
            # Upload file to S3
            with open(file_path, 'rb') as file:
                http.request(
                    'PUT', signature['url'], headers=signature['headers'],
                    body=file.read(),
                )

            print(f"Uploaded {file_path} to {signature['url']}")


if __name__ == '__main__':
    main()
