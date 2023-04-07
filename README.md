05 Bit Studio
=============

Website is built in collab with ChatGPT.

...

Development
-----------

Start virtualenv:

```bash
python3 -m venv .venv
source ./venv/bin/activate
pip install --upgrade pip pip-tools
pip-compile
pip install -r requirements.txt
```

Collab with ChatGPT:

```bash
python3 -m gptcollab.chat
```

or

```bash
python3 -m gptcollab.images
```
