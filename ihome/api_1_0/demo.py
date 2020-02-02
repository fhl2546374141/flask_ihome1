

from . import api
from ihome import db,models
from flask import current_app # 全局上下文的全局应用对象current_app

@api.route('/index')
def index():
    current_app.logger.error('fdsbuf')
    current_app.logger.warn('fdsbuf')
    current_app.logger.info('fdsbuf')
    current_app.logger.debug('fdsbuf')
    return 'Hello World!'