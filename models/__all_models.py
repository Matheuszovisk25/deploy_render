# models/__all_models.py

# Use SEMPRE o mesmo Base dos modelos:
from core.settings import DBBaseModel as Base  # <- importantíssimo!

# Importe todos os modelos para que registrem no metadata:
from models.user_model import UserModel
from models.producao_model import ProducaoModel
from models.processamento_model import ProcessamentoModel
from models.comercializacao_model import ComercializacaoModel  # confira o nome da classe
from models.exportacao_model import ExportacaoModel
from models.importacao_model import ImportacaoModel
