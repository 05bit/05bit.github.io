#!/usr/bin/env python3
from jinja2 import Environment, FileSystemLoader, select_autoescape


def main():
    build()


def build():
    jinja = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape()
    )
    template = jinja.get_template('index.html')
    html = template.render(
        message='Yo!'
    )
    print(html)


if __name__ == '__main__':
    main()

