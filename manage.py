#!/usr/bin/env python3
import argparse
import os
import urllib3
from mimetypes import guess_type
from umarkdown import markdown
from pydantic import BaseSettings
from signa import Factory as SignaFactory
from jinja2 import Environment, FileSystemLoader


class Settings(BaseSettings):
    htdocs_root: str = 'htdocs'
    content_root: str = 'content'
    templates_root: str = 'templates'
    pages: list = ['index.html']
    aws_access_key_id: str = ''
    aws_secret_access_key: str = ''
    s3_bucket: str = ''
    s3_region: str = 'us-west-001'
    s3_endpoint: str = 's3.{region}.backblazeb2.com'

    class Config:
        env_file = '.env'


def main():
    """Run site management command."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--build', action='store_true', help='Build')
    parser.add_argument('-p', '--publish', action='store_true', help='Publish')
    args = parser.parse_args()
    settings = Settings()
    if args.build:
        build(settings)
    elif args.publish:
        publish(settings)
    else:
        print(
            "Please specify either --build or --publish option. "
            "Use -h or --help for more information."
        )


def build(settings: Settings):
    """Build site."""
    pages = settings.pages
    content = render_md_files(settings)
    jinja = Environment(
        loader=FileSystemLoader(settings.templates_root), autoescape=False,
    )
    for name in pages:
        template = jinja.get_template(name)
        html = template.render(content=content)
        path = os.path.join(settings.htdocs_root, name)
        with open(path, 'w') as file:
            print(f"Writing {path}...")
            file.write(html)
            print("OK")


def publish(settings: Settings):
    """Publish to site S3."""
    upload_to_s3(settings)


def render_md_files(settings: Settings):
    """Render Markdown files to HTML files."""
    content_dir = settings.content_root
    rendered_dict = {}
    for filename in os.listdir(content_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(content_dir, filename)
            with open(file_path, 'r') as f:
                md_content = f.read()
                html_content = markdown(md_content)
                key = os.path.splitext(filename)[0]
                rendered_dict[key] = html_content
    return rendered_dict


def upload_to_s3(settings: Settings):
    """Upload files to S3."""
    assert settings.s3_region
    assert settings.s3_bucket
    assert settings.aws_access_key_id
    assert settings.aws_secret_access_key

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
                print(f"Uploading {file_path} to {signature['url']}...")
                http.request(
                    'PUT', signature['url'], headers=signature['headers'],
                    body=file.read(),
                )
            print("OK")


if __name__ == '__main__':
    main()
