import asyncio
import tornado

# 类 MainHander 处理 HTTP 请求
class MainHander(tornado.web.RequestHandler):
    # 定义get 请求的处理方法
    def get(self):
        self.write("Hello World")

# 函数 make_app 创建 Tornado 应用
def make_app():
    return tornado.web.Application([
        # 路由表 / MainHander
        (r"/", MainHander)
    ])

async def main():
    app = make_app()
    app.listen(8888) # 注册 HTTP 监听事件，动态产生 HTTP请求事件
    await asyncio.Event().wait() # wait 等待异步事件对象被 set (主协程挂起)

if __name__ == "__main__":
    '''
        程序初始状态：
        一个主协程（无其他协程）
        两个事件（主函数和HTTP监听，动态产生HTTP请求）
    '''
    asyncio.run(main()) # 创建一个事件循环