# yaml
npm i -g yaml-language-server @ansible/ansible-language-server

# toml
export PATH="$PATH:/root/.local/bin"

curl -fsSL https://github.com/tamasfe/taplo/releases/latest/download/taplo-linux-x86_64.gz \
  | gzip -d - | install -m 755 /dev/stdin /usr/local/bin/taplo
curl -fsSL https://tombi-toml.github.io/tombi/install.sh | sh

# python
python -m pip install -U pip ty ruff jedi-language-server python-lsp-server
