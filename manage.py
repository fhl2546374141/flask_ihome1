

from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand

from ihome import create_app,db

# 创建flask的应用对象
app = create_app('develop')
#　创建flask脚本管理工具
manager = Manager(app)
# 创建数据库迁移工具对象
Migrate(app,db)
#　向manger对象中添加数据库操作命令
manager.add_command('db',MigrateCommand)


if __name__ == '__main__':
    manager.run()
