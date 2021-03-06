# 数据库
* 添加数据库操作命令使用`Migrate`的`add_command`,第一个参数是想使用的命令名，第二个参数是`flask-migrat`e的`MigrateCommand`
* 当数据库模型变化的使用，使用`flask-migrate`做数据库的更新，分别执行`migrate`和`upgrade`。
* 定义数据库模型时候，参数`backref=‘example’`是向相应的模型里面添加一个example的属性，并且获取到的是模型对象。index设为True是为了给那一列创建索引，提升查询速度
* 一台PC使用`sqlite`，另一台使用`mysql`等，推送到git，在拉下来，重新做db migrate会出错 alembic.util.exc.CommandError: Can't locate revision identified by，
是因为`sqlite`会生成一个`alembic_version`的表，产生了冲突，解决方法是删掉`alembic_version`的所有数据

# 发送邮件
* 使用`flask-mail`发送邮件注意点：
1 所指定的发送者的邮箱需要开启`smtp`功能 
2 每个邮箱的`smtp`可以通过搜索引擎找到
3 配置中的`MAIL_PASSWORD`有可能是发送邮箱的密码(网易等)，还可能是此邮箱提供的一个单独的验证码(qq邮箱等)，具体看邮箱的说明
4 配置中的`MAIL_USERNAME`可以是去除尾部之后的用户名或者是邮箱账号
5 `MAIL_DEFAULT_SENDER`为默认的发送邮箱，或者在构建`Message`时候指定sender，sender结构为"发送者名 邮箱"发送这名可以省掉，或者是个元表(发送者名,邮箱)
6 还要注意是否打开`SSL`问题，如果打开，则配置里的端口要相应修改(各个邮箱不同，可以搜索找到)

# 用户确认
* 生成和检验token，可以分别使用`itsdangerous`包里的`dumps`和`loads`来实现。具体使用方法参看文档。
* 发送的确认邮件，内容是一个html格式的文件。其中包含一个跳转到自己网站的链接，然后在这个链接找到对应的路由函数，进而完成确认。
* 确认链接中一个注意点，就是相应的`url_for`需要一个参数赋值，`_external = True`,就可以生成完整的URL，包含协议，主机号，端口。确认的时候还需要将token作为链接的一部分传给视图函数进行处理。

# 请求钩子的使用
* 在请求之前或者之后调用的函数，可以避免视图函数中的重复代码。Flask中包含四个：
* `before_first_request`,`before_request`,`after_request`,`teardown_request`.功能查文档。
* 想在蓝图中使用针对程序全局请求的钩子，必须使用
* `befroe_app_request`等修饰器

# flask-login
* 提供了用户登陆，登出等功能

# CSS
* head中的link文件只被加载一次，刷新无效。因为上线以后，这部分东西一般是不需要改动的。开发的时候可以清除Chrome缓存的图片和文件，让link重新加载，就可以刷新了

# 用户头像
* 考虑使用Gravatar网站生成。
* 需要用到md5码，使用python标准库`hashlib`来生成
* 因为生成md5码是个CPU密集型操作，所以考虑将生成的md5码进行保存到数据库中，当email改变时再修改

# 模板
* 当不同的页面用到相同html的模块，可以把那部分独立写成一个html文件，并在需要引用的地方使用`include()`指令。`e.g：{% include '_posts.html' %}`，达到重用的目的
