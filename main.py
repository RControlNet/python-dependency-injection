from cndi.annotations import Bean, Autowired, AppInitilizer
from test_module.TestBean import TestBean

testBean = None


@Autowired()
def setTestBean(bean: TestBean):
    global testBean
    print(bean)
    testBean = bean


if __name__ == "__main__":
    app = AppInitilizer()
    app.componentScan("test_module")

    app.run()
    print(testBean.name)
    print(type(testBean))
