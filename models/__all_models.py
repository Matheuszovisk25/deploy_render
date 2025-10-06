
from sqlalchemy.orm import declarative_base
Base = declarative_base()

from models.user_model import UserModel
from models.producao_model import ProducaoModel
from models.processamento_model import ProcessamentoModel
from models.comercializacao_model import  ComercializacaooModel
from models.exportacao_model import ExportacaoModel
from models.importacao_model import ImportacaoModel
